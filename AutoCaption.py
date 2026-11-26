#!/usr/bin/env python3
"""
Auto Caption Plugin for DaVinci Resolve Free v21
Main entrypoint for internal Resolve script menu and standalone launcher.
"""

import os
import sys

# Locate root auto_captions project directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Check common installation locations
CANDIDATE_DIRS = [
    SCRIPT_DIR,
    os.path.dirname(SCRIPT_DIR),
    "/Users/nipunachandimal/Documents/Development/auto_captions",
    os.path.expanduser("~/Documents/Development/auto_captions"),
]

PROJECT_DIR = None
for d in CANDIDATE_DIRS:
    if os.path.exists(os.path.join(d, "core", "transcriber.py")):
        PROJECT_DIR = d
        break

if not PROJECT_DIR:
    PROJECT_DIR = "/Users/nipunachandimal/Documents/Development/auto_captions"

if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

def main():
    venv_python = os.path.join(PROJECT_DIR, "venv", "bin", "python3")

    # If running inside DaVinci Resolve
    is_inside_resolve = "resolve" in globals() or "fusion" in globals() or "bmd" in globals()
    
    if is_inside_resolve:
        from ui.fusion_ui import run_fusion_ui
        run_fusion_ui()
    else:
        # Check if running outside venv
        if os.path.exists(venv_python) and sys.executable != venv_python:
            import subprocess
            cmd = [venv_python, os.path.join(PROJECT_DIR, "ui", "desktop_gui.py")] + sys.argv[1:]
            sys.exit(subprocess.call(cmd))
        else:
            from ui.desktop_gui import main as gui_main
            gui_main()

if __name__ == "__main__":
    main()
