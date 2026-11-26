import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np
import torch

from core.transcriber import CaptionTranscriber


class FakeWhisperModel:
    dims = SimpleNamespace(n_mels=80)

    def __init__(self, language_probs):
        self.language_probs = language_probs
        self.transcribe_kwargs = None

    def detect_language(self, mel):
        return torch.tensor(0), self.language_probs

    def transcribe(self, audio_path, **kwargs):
        self.transcribe_kwargs = kwargs
        return {"segments": []}


class TranscriberLanguageTests(unittest.TestCase):
    def transcribe_with_language_probs(self, language, language_probs):
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as wav_file:
            wav_path = wav_file.name

        model = FakeWhisperModel(language_probs)
        transcriber = object.__new__(CaptionTranscriber)
        transcriber.model_size = "base"
        transcriber.language = language
        transcriber.device = "cpu"
        transcriber._model = model
        transcriber.extract_audio = lambda _: wav_path
        transcriber._load_model = lambda progress_callback=None: None

        try:
            with (
                patch("whisper.load_audio", return_value=np.zeros(16000, dtype=np.float32)),
                patch("whisper.pad_or_trim", side_effect=lambda audio: audio),
                patch("whisper.log_mel_spectrogram", return_value=torch.zeros((80, 3000))),
            ):
                transcriber.transcribe("input.mp4")
        finally:
            Path(wav_path).unlink(missing_ok=True)

        return model.transcribe_kwargs

    def test_auto_language_chooses_english_instead_of_unrelated_detection(self):
        kwargs = self.transcribe_with_language_probs(
            None,
            {"haw": 0.8, "en": 0.15, "si": 0.05},
        )

        self.assertEqual(kwargs["language"], "en")

    def test_auto_language_chooses_sinhala_when_it_scores_higher_than_english(self):
        kwargs = self.transcribe_with_language_probs(
            None,
            {"haw": 0.7, "en": 0.1, "si": 0.2},
        )

        self.assertEqual(kwargs["language"], "si")

    def test_explicit_language_skips_auto_detection(self):
        kwargs = self.transcribe_with_language_probs("si", {})

        self.assertEqual(kwargs["language"], "si")


if __name__ == "__main__":
    unittest.main()
