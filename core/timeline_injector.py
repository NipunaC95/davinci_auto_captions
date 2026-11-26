"""
DaVinci Resolve Timeline Integration and Direct Scripting Controller.
Supports both internal Resolve execution (Workspace > Scripts)
and external scripting connection.
"""

import os
import sys
import subprocess
import copy
import tempfile
import xml.etree.ElementTree as ET
from fractions import Fraction
from typing import Optional, List, Dict, Any

_DLL_DIRECTORY_HANDLES = []


def _fcpxml_time(value: str) -> Fraction:
    if not value.endswith("s"):
        raise ValueError(f"Invalid FCPXML time value: {value}")
    return Fraction(value[:-1])


def _format_fcpxml_time(value: Fraction) -> str:
    return f"{value.numerator}/{value.denominator}s"


def _write_overlay_timeline_xml(
    source_timeline_xml: str,
    captions_xml: str,
    output_path: str,
    timeline_name: str,
) -> None:
    timeline_tree = ET.parse(source_timeline_xml)
    captions_tree = ET.parse(captions_xml)
    timeline_root = timeline_tree.getroot()
    captions_root = captions_tree.getroot()

    timeline_sequence = timeline_root.find("./library/event/project/sequence")
    captions_sequence = captions_root.find("./library/event/project/sequence")
    timeline_resources = timeline_root.find("./resources")
    captions_resources = captions_root.find("./resources")
    if None in (timeline_sequence, captions_sequence, timeline_resources, captions_resources):
        raise ValueError("Timeline or captions XML is missing required FCPXML sections.")

    timeline_spine = timeline_sequence.find("./spine")
    captions_spine = captions_sequence.find("./spine")
    if timeline_spine is None or captions_spine is None:
        raise ValueError("Timeline or captions XML has no primary storyline.")

    title_effect = captions_resources.find("./effect")
    if title_effect is None:
        raise ValueError("Caption XML does not contain a title generator.")

    used_ids = {element.get("id") for element in timeline_resources.iter() if element.get("id")}
    effect_id = "r_caption_1"
    suffix = 1
    while effect_id in used_ids:
        suffix += 1
        effect_id = f"r_caption_{suffix}"
    copied_effect = copy.deepcopy(title_effect)
    copied_effect.set("id", effect_id)
    timeline_resources.append(copied_effect)

    sequence_start = _fcpxml_time(timeline_sequence.get("tcStart", "0s"))
    video_clips = []
    for element in timeline_spine:
        if element.tag != "asset-clip":
            continue
        start = _fcpxml_time(element.get("offset", "0s")) - sequence_start
        duration = _fcpxml_time(element.get("duration", "0s"))
        video_clips.append((start, start + duration, element))
    if not video_clips:
        raise ValueError("The active timeline has no video clips to place captions over.")

    titles_added = 0
    for title in captions_spine.findall("./title"):
        caption_start = _fcpxml_time(title.get("offset", "0s"))
        caption_duration = _fcpxml_time(title.get("duration", "0s"))
        caption_end = caption_start + caption_duration
        cursor = caption_start

        while cursor < caption_end:
            target = next(
                ((start, end, clip) for start, end, clip in video_clips if start <= cursor < end),
                None,
            )
            if target is None:
                raise ValueError(
                    f"Caption at {float(cursor):.2f}s falls outside the active timeline's video clips."
                )

            clip_start, clip_end, clip = target
            piece_end = min(caption_end, clip_end)
            overlay = copy.deepcopy(title)
            overlay.set("ref", effect_id)
            overlay.set("offset", _format_fcpxml_time(cursor - clip_start))
            overlay.set("duration", _format_fcpxml_time(piece_end - cursor))
            clip.append(overlay)
            titles_added += 1
            cursor = piece_end

    if titles_added == 0:
        raise ValueError("No caption title clips were found to add to the timeline.")

    event = timeline_root.find("./library/event")
    project = timeline_root.find("./library/event/project")
    if event is not None:
        event.set("name", timeline_name)
    if project is not None:
        project.set("name", timeline_name)

    timeline_tree.write(output_path, encoding="utf-8", xml_declaration=True)
    with open(output_path, "r", encoding="utf-8") as merged_file:
        xml_content = merged_file.read()
    declaration_end = xml_content.find("?>")
    xml_content = (
        xml_content[:declaration_end + 2]
        + "\n<!DOCTYPE fcpxml>"
        + xml_content[declaration_end + 2:]
    )
    with open(output_path, "w", encoding="utf-8") as merged_file:
        merged_file.write(xml_content)


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
        """Imports captions over the active video timeline, preserving the original."""
        proj = self.get_current_project()
        if not proj:
            return False
        mp = proj.GetMediaPool()
        if not mp:
            return False

        current_timeline = proj.GetCurrentTimeline()
        if current_timeline:
            with tempfile.TemporaryDirectory(prefix="autocaption_overlay_") as temp_dir:
                export_path = os.path.join(temp_dir, "source_timeline.fcpxml")
                if not current_timeline.Export(export_path, self.resolve.EXPORT_FCPXML_1_10, 0):
                    raise RuntimeError("Resolve could not export the active timeline for caption overlay.")
                source_timeline_xml = (
                    os.path.join(export_path, "Info.fcpxml")
                    if os.path.isdir(export_path)
                    else export_path
                )
                if not os.path.isfile(source_timeline_xml):
                    raise RuntimeError("Resolve did not produce the active timeline FCPXML export.")

                timeline_name = f"{current_timeline.GetName()}_with_Captions"
                merged_path = os.path.join(temp_dir, "timeline_with_captions.fcpxml")
                _write_overlay_timeline_xml(
                    source_timeline_xml,
                    xml_file_path,
                    merged_path,
                    timeline_name,
                )
                imported_timeline = mp.ImportTimelineFromFile(merged_path, {
                    "importSourceClips": False
                })
        else:
            imported_timeline = mp.ImportTimelineFromFile(xml_file_path, {
                "importSourceClips": False
            })
        return imported_timeline is not None
