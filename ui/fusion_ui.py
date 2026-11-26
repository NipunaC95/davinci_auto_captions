"""
Native DaVinci Resolve Fusion UI Script
Appears under Workspace > Scripts > Utility > AutoCaption
"""

import os
import sys
import json
import subprocess
import tempfile

def run_fusion_ui():
    """Runs the native Fusion UI dialog or launches the standalone studio GUI."""
    project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    venv_py = os.path.join(project_dir, "venv", "bin", "python3")
    desktop_app_script = os.path.join(project_dir, "ui", "desktop_gui.py")

    # Get Resolve globals if available
    fu = globals().get("fusion")
    bmd = globals().get("bmd")
    resolve = globals().get("resolve")

    if not fu or not bmd or not resolve:
        # Fallback to standalone desktop GUI
        py_exe = venv_py if os.path.exists(venv_py) else sys.executable
        subprocess.Popen([py_exe, desktop_app_script])
        return

    # Check active project and timeline
    pm = resolve.GetProjectManager()
    proj = pm.GetCurrentProject() if pm else None
    timeline = proj.GetCurrentTimeline() if proj else None

    timeline_name = timeline.GetName() if timeline else "No Active Timeline"
    found_media = []

    if timeline:
        for t_type in ["video", "audio"]:
            count = timeline.GetTrackCount(t_type)
            for idx in range(1, count + 1):
                items = timeline.GetItemListInTrack(t_type, idx) or []
                for item in items:
                    mp_item = item.GetMediaPoolItem()
                    if mp_item:
                        props = mp_item.GetClipProperty()
                        fp = props.get("File Path", "")
                        if fp and os.path.exists(fp) and fp not in found_media:
                            found_media.append(fp)

    media_display = os.path.basename(found_media[0]) if found_media else "No media clips detected on timeline"

    ui = fu.UIManager
    disp = bmd.UIDispatcher(ui)

    style_names = [
        "Hormozi Viral",
        "TikTok Bounce",
        "MrBeast Highlighter",
        "Cinematic Box",
        "Cyber Neon",
        "Clean Minimalist",
        "Retro Comic Pop",
        "Split Tone"
    ]

    win = disp.AddWindow({
        "WindowTitle": "⚡ Auto Caption Studio — DaVinci Resolve v21",
        "ID": "AutoCapWin",
        "Geometry": [350, 250, 520, 480],
    }, [
        ui.VGroup({"Spacing": 8}, [
            ui.Label({
                "Text": "⚡ Auto Caption for DaVinci Resolve Free v21",
                "Weight": 0.5,
                "Font": ui.Font({"PixelSize": 16, "Bold": True}),
                "Alignment": {"AlignHCenter": True}
            }),
            ui.Label({
                "Text": "Transcribes speech & generates animated Text+ caption clips",
                "Weight": 0.5,
                "Font": ui.Font({"PixelSize": 10}),
                "Alignment": {"AlignHCenter": True}
            }),
            ui.VGap(4),

            # Status Box
            ui.Label({"Text": f"Active Timeline: {timeline_name}", "Font": ui.Font({"Bold": True})}),
            ui.Label({"Text": f"Source Media: {media_display}", "Font": ui.Font({"PixelSize": 10})}),
            ui.VGap(6),

            # Style Selection
            ui.Label({"Text": "Select Drag-and-Drop Caption Style:", "Font": ui.Font({"Bold": True})}),
            ui.ComboBox({"ID": "StyleCombo"}),

            # Chunking Selection
            ui.Label({"Text": "Words per Caption Clip:", "Font": ui.Font({"Bold": True})}),
            ui.ComboBox({"ID": "ChunkCombo"}),

            # AI Model
            ui.Label({"Text": "Whisper AI Model:", "Font": ui.Font({"Bold": True})}),
            ui.ComboBox({"ID": "ModelCombo"}),

            ui.VGap(10),
            # Actions
            ui.Button({"ID": "QuickCaptionBtn", "Text": "⚡ Auto-Caption Active Timeline Now", "Weight": 1.5}),
            ui.Button({"ID": "LaunchStudioBtn", "Text": "🚀 Open Caption Studio (Interactive Table & Word Editor)", "Weight": 1.5}),
            ui.Button({"ID": "CloseBtn", "Text": "Close"}),
        ])
    ])

    itm = win.GetItems()

    for s in style_names:
        itm["StyleCombo"].AddItem(s)

    chunks = [
        "short (2-3 words, TikTok/Reels)",
        "1_word (Punchy)",
        "balanced (4-6 words)",
        "sentence (Full Sentences)"
    ]
    for c in chunks:
        itm["ChunkCombo"].AddItem(c)

    for m in ["base (Recommended - Fast & Accurate)", "tiny (Fastest)", "small (High Accuracy)"]:
        itm["ModelCombo"].AddItem(m)

    def on_close(ev):
        disp.ExitLoop()

    def on_launch_studio(ev):
        disp.ExitLoop()
        py_exe = venv_py if os.path.exists(venv_py) else sys.executable
        subprocess.Popen([py_exe, desktop_app_script])

    def on_quick_caption(ev):
        if not found_media:
            # If no timeline media, launch studio to browse a file
            disp.ExitLoop()
            py_exe = venv_py if os.path.exists(venv_py) else sys.executable
            subprocess.Popen([py_exe, desktop_app_script])
            return

        media_file = found_media[0]
        style_idx = itm["StyleCombo"].CurrentIndex
        chosen_style = style_names[style_idx] if 0 <= style_idx < len(style_names) else "Hormozi Viral"

        chunk_raw = itm["ChunkCombo"].CurrentText
        chunk_mode = "short"
        if "1_word" in chunk_raw:
            chunk_mode = "1_word"
        elif "balanced" in chunk_raw:
            chunk_mode = "balanced"
        elif "sentence" in chunk_raw:
            chunk_mode = "sentence"

        model_raw = itm["ModelCombo"].CurrentText
        model_name = "base"
        if "tiny" in model_raw:
            model_name = "tiny"
        elif "small" in model_raw:
            model_name = "small"

        disp.ExitLoop()

        # Run background transcription script that creates FCPXML and imports into Resolve
        cli_runner = os.path.join(project_dir, "core", "quick_caption.py")
        py_exe = venv_py if os.path.exists(venv_py) else sys.executable
        subprocess.Popen([
            py_exe, cli_runner,
            "--media", media_file,
            "--style", chosen_style,
            "--chunk", chunk_mode,
            "--model", model_name,
            "--auto-import"
        ])

    win.On.AutoCapWin.Close = on_close
    win.On.CloseBtn.Clicked = on_close
    win.On.LaunchStudioBtn.Clicked = on_launch_studio
    win.On.QuickCaptionBtn.Clicked = on_quick_caption

    win.Show()
    disp.RunLoop()
    win.Hide()

if __name__ == "__main__":
    run_fusion_ui()
