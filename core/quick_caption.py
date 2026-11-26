#!/usr/bin/env python3
"""
Quick Caption CLI runner for one-click transcription and timeline injection.
"""

import os
import sys
import argparse
import subprocess
import tempfile

# Ensure project root is in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.transcriber import CaptionTranscriber, export_srt
from core.xml_generator import generate_fcpxml
from core.timeline_injector import ResolveBridge

def notify_user(title: str, message: str):
    """Sends a native macOS notification banner."""
    if sys.platform == "darwin":
        script = f'display notification "{message}" with title "{title}"'
        try:
            subprocess.run(["osascript", "-e", script], check=False)
        except Exception:
            pass

def main():
    parser = argparse.ArgumentParser(description="Quick Caption Runner")
    parser.add_argument("--media", required=True, help="Path to input media file")
    parser.add_argument("--style", default="Hormozi Viral", help="Caption style preset name")
    parser.add_argument("--chunk", default="short", help="Chunking mode: 1_word, short, balanced, sentence")
    parser.add_argument("--casing", default="UPPERCASE", help="Casing: UPPERCASE, Title Case, Original")
    parser.add_argument("--model", default="base", help="Whisper model: tiny, base, small")
    parser.add_argument("--auto-import", action="store_true", help="Automatically import into active Resolve project")

    args = parser.parse_args()

    notify_user("Auto Caption", f"Transcribing '{os.path.basename(args.media)}' with {args.style} style...")

    transcriber = CaptionTranscriber(model_size=args.model)
    segments = transcriber.transcribe(
        media_path=args.media,
        chunk_mode=args.chunk,
        casing=args.casing
    )

    if not segments:
        notify_user("Auto Caption", "No speech detected in audio!")
        return

    # Output paths in user's Movies folder or temp
    movies_dir = os.path.expanduser("~/Movies")
    if not os.path.exists(movies_dir):
        movies_dir = tempfile.gettempdir()

    safe_style = args.style.replace(" ", "_")
    xml_path = os.path.join(movies_dir, f"Captions_{safe_style}.fcpxml")
    srt_path = os.path.join(movies_dir, f"Captions_{safe_style}.srt")

    generate_fcpxml(
        segments=segments,
        output_path=xml_path,
        fps=30.0,
        style_name=args.style,
        timeline_name=f"Captions_{args.style}"
    )
    export_srt(segments, srt_path)

    # Attempt automatic timeline import if requested
    bridge = ResolveBridge()
    imported = False
    if args.auto_import and bridge.is_connected():
        imported = bridge.import_timeline_xml(xml_path)

    if imported:
        notify_user("Auto Caption Complete", f"Created {len(segments)} caption clips in DaVinci Resolve!")
    else:
        notify_user("Auto Caption Ready", f"Saved {len(segments)} clips to: {os.path.basename(xml_path)}")
        # If running on macOS, reveal the file in Finder so the user can drag it directly into Resolve!
        if sys.platform == "darwin":
            subprocess.run(["open", "-R", xml_path], check=False)

if __name__ == "__main__":
    main()
