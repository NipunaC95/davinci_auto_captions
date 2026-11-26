#!/usr/bin/env python3
"""
Auto Caption Plugin for DaVinci Resolve Free v21
Main entrypoint for both internal Resolve scripts and standalone execution.
"""

import os
import sys

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    venv_python = os.path.join(base_dir, "venv", "bin", "python3")

    # If running inside DaVinci Resolve
    if "resolve" in globals() or "fusion" in globals():
        from ui.fusion_ui import run_fusion_ui
        run_fusion_ui()
    else:
        # Check if we are running in the venv
        if os.path.exists(venv_python) and sys.executable != venv_python:
            # Re-execute with virtualenv python to guarantee all libraries are loaded
            import subprocess
            cmd = [venv_python, os.path.join(base_dir, "ui", "desktop_gui.py")] + sys.argv[1:]
            sys.exit(subprocess.call(cmd))
        else:
            from ui.desktop_gui import main as gui_main
            gui_main()

if __name__ == "__main__":
    main()
