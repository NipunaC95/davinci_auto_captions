#!/usr/bin/env python3
"""
Auto Caption Plugin for DaVinci Resolve Free v21
Main entrypoint for internal Resolve script menu and standalone launcher.
"""

import os
import subprocess
import sys

# Locate root auto_captions project directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_MARKER = os.path.join(SCRIPT_DIR, "AutoCaption.project")
CANDIDATE_DIRS = []
if os.path.isfile(PROJECT_MARKER):
    with open(PROJECT_MARKER, "r", encoding="utf-8") as marker:
        CANDIDATE_DIRS.append(marker.read().strip())
# Check common installation locations
CANDIDATE_DIRS.extend([
    SCRIPT_DIR,
    os.path.dirname(SCRIPT_DIR),
])

PROJECT_DIR = None
for d in CANDIDATE_DIRS:
    if os.path.exists(os.path.join(d, "core", "transcriber.py")):
        PROJECT_DIR = d
        break

if not PROJECT_DIR:
    PROJECT_DIR = SCRIPT_DIR

if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

def load_resolve_scripting_module():
    if sys.platform.startswith("win"):
        modules_dir = os.path.join(
            os.getenv("PROGRAMDATA", r"C:\ProgramData"),
            "Blackmagic Design",
            "DaVinci Resolve",
            "Support",
            "Developer",
            "Scripting",
            "Modules",
        )
        if os.path.isdir(modules_dir) and modules_dir not in sys.path:
            sys.path.insert(0, modules_dir)

        if not os.environ.get("RESOLVE_SCRIPT_LIB"):
            command = (
                "$p = Get-Process -Name Resolve -ErrorAction Stop | "
                "Select-Object -First 1 -ExpandProperty Path; "
                "if ($p) { Split-Path -Parent $p }"
            )
            result = subprocess.run(
                ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", command],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode == 0 and result.stdout.strip():
                resolve_dir = result.stdout.strip().splitlines()[-1]
                library = os.path.join(resolve_dir, "fusionscript.dll")
                if os.path.isfile(library):
                    os.environ["RESOLVE_SCRIPT_LIB"] = library
                    os.environ["PATH"] = resolve_dir + os.pathsep + os.environ.get("PATH", "")

    import DaVinciResolveScript as scripting_module
    return scripting_module


def show_launcher_error(message):
    print(f"[AutoCaption] {message}")
    if sys.platform.startswith("win"):
        import ctypes
        ctypes.windll.user32.MessageBoxW(None, message, "Auto Caption Studio", 0x10)


def main():
    os.environ["AUTO_CAPTION_PROJECT_DIR"] = PROJECT_DIR
    if sys.platform.startswith("win"):
        venv_python = os.path.join(PROJECT_DIR, "venv", "Scripts", "python.exe")
    else:
        venv_python = os.path.join(PROJECT_DIR, "venv", "bin", "python3")

    # If running inside DaVinci Resolve
    resolve_app = globals().get("resolve")
    fusion_app = globals().get("fusion")
    scripting_module = globals().get("bmd")
    is_resolve_script = os.path.basename(
        os.path.dirname(os.path.dirname(SCRIPT_DIR))
    ).lower() == "fusion"
    is_inside_resolve = bool(resolve_app or fusion_app or scripting_module)
    
    if is_inside_resolve or is_resolve_script:
        if not scripting_module:
            try:
                scripting_module = load_resolve_scripting_module()
            except ImportError as error:
                show_launcher_error(f"Could not load the Resolve scripting API: {error}")
                return
        if scripting_module and not resolve_app:
            resolve_app = scripting_module.scriptapp("Resolve")
        if scripting_module and not fusion_app:
            fusion_app = scripting_module.scriptapp("Fusion")
        if not (resolve_app and fusion_app and scripting_module):
            show_launcher_error(
                "Could not connect to Resolve/Fusion. Make sure Resolve is open, then run "
                "Workspace > Scripts > Utility > AutoCaption."
            )
            return

        from ui.fusion_ui import run_fusion_ui
        run_fusion_ui(
            fusion_app=fusion_app,
            scripting_module=scripting_module,
            resolve_app=resolve_app,
        )
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
