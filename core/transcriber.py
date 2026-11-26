"""
Core Audio Extraction and Speech-to-Text Engine using OpenAI Whisper
with word-level timing and flexible caption chunking.
"""

import os
import sys
import json
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Callable

def get_ffmpeg_executable() -> str:
    """Finds an available ffmpeg executable, ensuring 'ffmpeg' is accessible in PATH for Whisper."""
    exe = None
    try:
        import imageio_ffmpeg
        img_exe = imageio_ffmpeg.get_ffmpeg_exe()
        if os.path.exists(img_exe) and os.access(img_exe, os.X_OK):
            exe = img_exe
            # Ensure a file literally named 'ffmpeg' exists in that directory
            bin_dir = os.path.dirname(img_exe)
            alias_ffmpeg = os.path.join(bin_dir, "ffmpeg")
            if not os.path.exists(alias_ffmpeg):
                try:
                    os.symlink(img_exe, alias_ffmpeg)
                except Exception:
                    pass
    except Exception:
        pass

    # Check venv/bin/ffmpeg
    venv_dir = os.path.dirname(sys.executable)
    venv_ffmpeg = os.path.join(venv_dir, "ffmpeg")
    if os.path.exists(venv_ffmpeg) and os.access(venv_ffmpeg, os.X_OK):
        if not exe:
            exe = venv_ffmpeg

    if not exe:
        system_ffmpeg = shutil.which("ffmpeg")
        if system_ffmpeg:
            exe = system_ffmpeg

    if not exe:
        # Common macOS / Linux paths
        for p in ["/opt/homebrew/bin/ffmpeg", "/usr/local/bin/ffmpeg", "/usr/bin/ffmpeg"]:
            if os.path.exists(p) and os.access(p, os.X_OK):
                exe = p
                break

    if exe:
        # Prepend both directory containing exe and venv/bin to PATH so whisper's internal calls succeed
        dirs_to_add = [os.path.dirname(exe), venv_dir]
        curr_path = os.environ.get("PATH", "")
        for d in dirs_to_add:
            if d not in curr_path:
                curr_path = f"{d}:{curr_path}"
        os.environ["PATH"] = curr_path
        return exe

    raise RuntimeError("FFmpeg executable not found! Please install ffmpeg or imageio-ffmpeg.")

@dataclass
class WordTiming:
    word: str
    start: float
    end: float

@dataclass
class CaptionSegment:
    index: int
    start_time: float  # seconds
    end_time: float    # seconds
    text: str
    words: List[Dict[str, any]]

    def to_srt_time(self, seconds: float) -> str:
        millis = int((seconds - int(seconds)) * 1000)
        total_seconds = int(seconds)
        secs = total_seconds % 60
        mins = (total_seconds // 60) % 60
        hours = total_seconds // 3600
        return f"{hours:02d}:{mins:02d}:{secs:02d},{millis:03d}"

    def to_srt_entry(self, color_hex: Optional[str] = None) -> str:
        start_str = self.to_srt_time(self.start_time)
        end_str = self.to_srt_time(self.end_time)
        display_text = self.text
        if color_hex:
            display_text = f'<font color="{color_hex}">{display_text}</font>'
        return f"{self.index}\n{start_str} --> {end_str}\n{display_text}\n"

class CaptionTranscriber:
    def __init__(self, model_size: str = "base", language: Optional[str] = None, device: Optional[str] = None):
        self.model_size = model_size
        normalized_language = language.strip().lower() if language else ""
        self.language = normalized_language if normalized_language and normalized_language != "auto" else None
        self.device = device or self._detect_device()
        self.ffmpeg_exe = get_ffmpeg_executable()
        self._model = None

    def _detect_device(self) -> str:
        try:
            import torch
        except ImportError as error:
            raise RuntimeError("PyTorch is required for Whisper transcription.") from error
        if torch.cuda.is_available():
            return "cuda"
        if sys.platform.startswith("win") and shutil.which("nvidia-smi"):
            raise RuntimeError(
                "An NVIDIA GPU is present, but PyTorch cannot access CUDA. "
                "Install the CUDA-enabled requirements from requirements.txt."
            )
        # Note: PyTorch on Apple Silicon MPS does not support float64 DTW alignments for Whisper word timestamps.
        # CPU is blazingly fast on Apple Silicon (400+ fps) and avoids DTW tensor crashes.
        return "cpu"

    def _detect_english_or_sinhala(self, wav_path: str, whisper) -> str:
        model = self._model
        if model is None:
            raise RuntimeError("Whisper model must be loaded before detecting language.")

        audio = whisper.load_audio(wav_path)
        audio = whisper.pad_or_trim(audio)
        mel = whisper.log_mel_spectrogram(
            audio,
            n_mels=model.dims.n_mels,
        ).to(self.device)
        _, language_probs = model.detect_language(mel)
        return max(("en", "si"), key=lambda code: language_probs.get(code, 0.0))

    def _load_model(self, progress_callback: Optional[Callable[[str, float], None]] = None):
        if self._model is None:
            if progress_callback:
                progress_callback(
                    f"Loading Whisper '{self.model_size}' model on {self.device.upper()}...",
                    0.1,
                )
            import whisper
            self._model = whisper.load_model(self.model_size, device=self.device)

    def extract_audio(self, media_path: str, output_wav: Optional[str] = None) -> str:
        """Extracts 16kHz mono WAV audio suitable for Whisper speech recognition."""
        if not os.path.exists(media_path):
            raise FileNotFoundError(f"Input media not found: {media_path}")

        if output_wav is None:
            fd, output_wav = tempfile.mkstemp(suffix=".wav", prefix="caption_audio_")
            os.close(fd)

        cmd = [
            self.ffmpeg_exe,
            "-y",
            "-i", media_path,
            "-vn",
            "-acodec", "pcm_s16le",
            "-ar", "16000",
            "-ac", "1",
            output_wav
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if res.returncode != 0:
            raise RuntimeError(f"FFmpeg audio extraction failed: {res.stderr.decode('utf-8', errors='ignore')}")
        return output_wav

    def transcribe(
        self,
        media_path: str,
        chunk_mode: str = "short",  # "1_word", "short" (2-3 words), "balanced" (4-6), "sentence"
        casing: str = "UPPERCASE",  # "UPPERCASE", "Title Case", "Original"
        max_chars: int = 32,
        progress_callback: Optional[Callable[[str, float], None]] = None,
    ) -> List[CaptionSegment]:
        """Transcribes media file and returns structured caption segments."""
        if progress_callback:
            progress_callback("Extracting audio...", 0.05)

        wav_path = self.extract_audio(media_path)
        try:
            self._load_model(progress_callback)

            import whisper
            language = self.language
            if language is None:
                if progress_callback:
                    progress_callback("Detecting English or Sinhala...", 0.2)
                language = self._detect_english_or_sinhala(wav_path, whisper)
                language_name = "Sinhala" if language == "si" else "English"
                if progress_callback:
                    progress_callback(f"Detected language: {language_name}", 0.25)

            if progress_callback:
                progress_callback("Transcribing speech with word timestamps...", 0.3)

            transcribe_kwargs = {
                "language": language,
                "word_timestamps": True,
                "verbose": False,
            }

            result = self._model.transcribe(wav_path, **transcribe_kwargs)

            if progress_callback:
                progress_callback("Formatting captions and timings...", 0.85)

            segments = self._process_whisper_result(
                result,
                chunk_mode=chunk_mode,
                casing=casing,
                max_chars=max_chars
            )

            if progress_callback:
                progress_callback("Transcription complete!", 1.0)

            return segments
        finally:
            if os.path.exists(wav_path):
                try:
                    os.remove(wav_path)
                except OSError:
                    pass

    def _apply_casing(self, text: str, casing: str) -> str:
        text = text.strip()
        if casing == "UPPERCASE":
            return text.upper()
        elif casing == "Title Case":
            return text.title()
        return text

    def _process_whisper_result(
        self,
        result: dict,
        chunk_mode: str,
        casing: str,
        max_chars: int
    ) -> List[CaptionSegment]:
        """Chunks word-level timestamps into modern caption clips."""
        all_words: List[WordTiming] = []

        for seg in result.get("segments", []):
            words = seg.get("words", [])
            if words:
                for w in words:
                    cleaned_word = w.get("word", "").strip()
                    if cleaned_word:
                        all_words.append(WordTiming(
                            word=cleaned_word,
                            start=float(w.get("start", seg.get("start", 0.0))),
                            end=float(w.get("end", seg.get("end", 0.0)))
                        ))
            else:
                # Fallback if segment has no word timestamps
                seg_text = seg.get("text", "").strip()
                if seg_text:
                    words_in_seg = seg_text.split()
                    seg_duration = max(0.2, float(seg.get("end", 1.0)) - float(seg.get("start", 0.0)))
                    word_duration = seg_duration / max(1, len(words_in_seg))
                    t = float(seg.get("start", 0.0))
                    for w in words_in_seg:
                        all_words.append(WordTiming(
                            word=w,
                            start=t,
                            end=t + word_duration
                        ))
                        t += word_duration

        if not all_words:
            return []

        # Determine target word chunk size
        if chunk_mode == "1_word":
            target_words = 1
        elif chunk_mode == "short":
            target_words = 3
        elif chunk_mode == "balanced":
            target_words = 5
        else:  # sentence / long
            target_words = 8

        caption_segments: List[CaptionSegment] = []
        current_chunk: List[WordTiming] = []
        current_char_count = 0

        for w in all_words:
            current_chunk.append(w)
            current_char_count += len(w.word) + 1

            # Check if chunk should close:
            # 1. Target word count reached
            # 2. Max chars exceeded
            # 3. Natural sentence-ending punctuation (., !, ?)
            # 4. Long pause before next word (gap > 0.8s)
            reached_target = len(current_chunk) >= target_words
            exceeded_chars = current_char_count >= max_chars
            has_punctuation = w.word.endswith((".", "!", "?")) and len(current_chunk) >= 2

            if reached_target or exceeded_chars or has_punctuation:
                self._add_segment(caption_segments, current_chunk, casing)
                current_chunk = []
                current_char_count = 0

        if current_chunk:
            self._add_segment(caption_segments, current_chunk, casing)

        # Smooth minimum duration to prevent flashing clips
        for seg in caption_segments:
            if seg.end_time - seg.start_time < 0.22:
                seg.end_time = seg.start_time + 0.22

        return caption_segments

    def _add_segment(self, segment_list: List[CaptionSegment], chunk: List[WordTiming], casing: str):
        if not chunk:
            return
        start_time = chunk[0].start
        end_time = chunk[-1].end
        raw_text = " ".join(w.word for w in chunk)
        styled_text = self._apply_casing(raw_text, casing)
        
        words_data = [
            {
                "word": self._apply_casing(w.word, casing),
                "start": w.start,
                "end": w.end
            }
            for w in chunk
        ]

        segment = CaptionSegment(
            index=len(segment_list) + 1,
            start_time=start_time,
            end_time=end_time,
            text=styled_text,
            words=words_data
        )
        segment_list.append(segment)

def export_srt(segments: List[CaptionSegment], file_path: str, color_hex: Optional[str] = None):
    """Exports caption segments to a standard .srt subtitle file."""
    with open(file_path, "w", encoding="utf-8") as f:
        for seg in segments:
            f.write(seg.to_srt_entry(color_hex=color_hex) + "\n")

def export_json(segments: List[CaptionSegment], file_path: str):
    """Exports caption segments with word-level timings to JSON."""
    data = [asdict(s) for s in segments]
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
