"""
DaVinci Resolve Timeline Integration and Direct Scripting Controller.
Supports both internal Resolve execution (Workspace > Scripts)
and external scripting connection.
"""

import os
import sys
import subprocess
from typing import Optional, List, Dict, Any

_DLL_DIRECTORY_HANDLES = []


def _prepare_resolve_scripting():
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

        if not os.getenv("RESOLVE_SCRIPT_LIB"):
            command = (
                "$p = Get-Process -Name Resolve -ErrorAction Stop | "
                "Select-Object -First 1 -ExpandProperty Path; "
                "if ($p) { Split-Path -Parent $p }"
            )
            try:
                result = subprocess.run(
                    ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", command],
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=5,
                )
            except (OSError, subprocess.SubprocessError) as error:
                print(f"[AutoCaption] Could not locate Resolve's scripting library: {error}")
                return

            if result.returncode != 0 or not result.stdout.strip():
                return

            resolve_dir = result.stdout.strip().splitlines()[-1]
            script_library = os.path.join(resolve_dir, "fusionscript.dll")
            if os.path.isfile(script_library):
                os.environ["RESOLVE_SCRIPT_LIB"] = script_library
                os.environ["PATH"] = resolve_dir + os.pathsep + os.environ.get("PATH", "")
                if hasattr(os, "add_dll_directory"):
                    _DLL_DIRECTORY_HANDLES.append(os.add_dll_directory(resolve_dir))
    elif sys.platform.startswith("darwin"):
        modules_dir = "/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting/Modules"
        if modules_dir not in sys.path:
            sys.path.insert(0, modules_dir)
    elif sys.platform.startswith("linux"):
        modules_dir = "/opt/resolve/Developer/Scripting/Modules"
        if modules_dir not in sys.path:
            sys.path.insert(0, modules_dir)


def is_resolve_running() -> bool:
    """Checks if the DaVinci Resolve process is currently running on the system."""
    try:
        if sys.platform == "darwin" or sys.platform.startswith("linux"):
            out = subprocess.check_output(["ps", "-A"], text=True)
            return any("Resolve.app" in line or "/Resolve" in line for line in out.splitlines() if "grep" not in line)
        elif sys.platform.startswith("win"):
            out = subprocess.check_output(["tasklist"], text=True)
            return "Resolve.exe" in out
    except Exception:
        pass
    return False

def get_resolve_instance():
    """Returns the active DaVinci Resolve script application instance."""
    # 1. Check if running inside DaVinci Resolve (resolve is already in globals)
    if "resolve" in globals():
        return globals()["resolve"]
    
    _prepare_resolve_scripting()

    # 2. Try importing DaVinciResolveScript
    try:
        import DaVinciResolveScript as bmd
        return bmd.scriptapp("Resolve")
    except ImportError as error:
        print(f"[AutoCaption] Could not load the Resolve scripting API: {error}")

    return None

class ResolveBridge:
    def __init__(self, resolve_app=None):
        self.resolve = resolve_app or get_resolve_instance()
        self.running = is_resolve_running()

    def is_connected(self) -> bool:
        return self.resolve is not None

    def is_running(self) -> bool:
        return self.running or is_resolve_running()

    def refresh_connection(self) -> bool:
        """Re-check the Resolve scripting API after Resolve or external scripting starts."""
        self.resolve = get_resolve_instance()
        self.running = is_resolve_running()
        return self.is_connected()

    def get_project_manager(self):
        if not self.resolve:
            return None
        return self.resolve.GetProjectManager()

    def get_current_project(self):
        pm = self.get_project_manager()
        if not pm:
            return None
        return pm.GetCurrentProject()

    def get_current_timeline(self):
        proj = self.get_current_project()
        if not proj:
            return None
        return proj.GetCurrentTimeline()

    def get_timeline_info(self) -> Dict[str, Any]:
        """Returns metadata about the active timeline (framerate, dimensions, source files)."""
        timeline = self.get_current_timeline()
        if not timeline:
            return {}

        proj = self.get_current_project()
        
        # Determine framerate
        fps = 30.0
        try:
            fps_str = proj.GetSetting("timelineFrameRate")
            if fps_str:
                fps = float(fps_str)
        except Exception:
            pass

        # Timeline dimensions
        width = 1920
        height = 1080
        try:
            w_str = proj.GetSetting("timelineResolutionWidth")
            h_str = proj.GetSetting("timelineResolutionHeight")
            if w_str and h_str:
                width = int(w_str)
                height = int(h_str)
        except Exception:
            pass

        # Collect source media files from timeline clips
        source_files = []
        track_types = ["video", "audio"]
        for t_type in track_types:
            count = timeline.GetTrackCount(t_type)
            for idx in range(1, count + 1):
                items = timeline.GetItemListInTrack(t_type, idx) or []
                for item in items:
                    mp_item = item.GetMediaPoolItem()
                    if mp_item:
                        clip_props = mp_item.GetClipProperty()
                        file_path = clip_props.get("File Path", "")
                        if file_path and os.path.exists(file_path) and file_path not in source_files:
                            source_files.append(file_path)

        return {
            "name": timeline.GetName(),
            "fps": fps,
            "width": width,
            "height": height,
            "start_frame": timeline.GetStartFrame(),
            "end_frame": timeline.GetEndFrame(),
            "source_files": source_files
        }

    def import_timeline_xml(self, xml_file_path: str) -> bool:
        """Imports an FCPXML / XML timeline into the active DaVinci Resolve project."""
        proj = self.get_current_project()
        if not proj:
            return False
        mp = proj.GetMediaPool()
        if not mp:
            return False
        
        # Import timeline from XML
        imported_timeline = mp.ImportTimelineFromFile(xml_file_path, {
            "importSourceClips": False
        })
        return imported_timeline is not None
