"""
Native DaVinci Resolve Fusion UI Script
Appears under Workspace > Scripts > Utility > AutoCaption
"""

import os
import sys
import subprocess

def run_fusion_ui():
    """Runs the native Fusion UI dialog or launches the standalone studio GUI."""
    script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    venv_py = os.path.join(script_dir, "venv", "bin", "python3")
    desktop_app_script = os.path.join(script_dir, "ui", "desktop_gui.py")

    # If running inside DaVinci Resolve with Fusion UI available
    fu = globals().get("fusion")
    bmd = globals().get("bmd")
    resolve = globals().get("resolve")

    if not fu or not bmd:
        # Fallback to standalone desktop GUI
        py_exe = venv_py if os.path.exists(venv_py) else sys.executable
        subprocess.Popen([py_exe, desktop_app_script])
        return

    ui = fu.UIManager
    disp = bmd.UIDispatcher(ui)

    # Styles list
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
        "WindowTitle": "Auto Caption Studio — DaVinci Resolve v21",
        "ID": "AutoCapWin",
        "Geometry": [350, 250, 480, 420],
    }, [
        ui.VGroup({"Spacing": 10}, [
            ui.Label({
                "Text": "⚡ Auto Caption for DaVinci Resolve v21",
                "Weight": 0.5,
                "Font": ui.Font({"PixelSize": 15, "Bold": True}),
                "Alignment": {"AlignHCenter": True}
            }),
            ui.Label({
                "Text": "Generate animated word captions for DaVinci Resolve Free & Studio",
                "Weight": 0.5,
                "Font": ui.Font({"PixelSize": 10}),
                "Alignment": {"AlignHCenter": True}
            }),

            # Style Selection
            ui.Label({"Text": "Choose Caption Style Preset:", "Font": ui.Font({"Bold": True})}),
            ui.ComboBox({"ID": "StyleCombo"}),

            # Chunking Selection
            ui.Label({"Text": "Caption Length (Words per Clip):", "Font": ui.Font({"Bold": True})}),
            ui.ComboBox({"ID": "ChunkCombo"}),

            # Whisper Model Selection
            ui.Label({"Text": "Speech Recognition AI Model:", "Font": ui.Font({"Bold": True})}),
            ui.ComboBox({"ID": "ModelCombo"}),

            # Buttons
            ui.VGap(10),
            ui.Button({"ID": "LaunchStudioBtn", "Text": "🚀 Open Full Caption Studio (GUI & Editor)", "Weight": 1.5}),
            ui.Button({"ID": "QuickCaptionBtn", "Text": "⚡ Quick Caption Active Timeline", "Weight": 1.5}),
            ui.Button({"ID": "CloseBtn", "Text": "Close"}),
        ])
    ])

    itm = win.GetItems()

    # Populate Combos
    for s in style_names:
        itm["StyleCombo"].AddItem(s)

    for c in ["short (2-3 words, TikTok/Reels)", "1_word (Punchy)", "balanced (4-6 words)", "sentence"]:
        itm["ChunkCombo"].AddItem(c)

    for m in ["base (Recommended - Fast & Accurate)", "tiny (Fastest)", "small (High Accuracy)", "medium"]:
        itm["ModelCombo"].AddItem(m)

    # Event handlers
    def on_close(ev):
        disp.ExitLoop()

    def on_launch_studio(ev):
        disp.ExitLoop()
        py_exe = venv_py if os.path.exists(venv_py) else sys.executable
        subprocess.Popen([py_exe, desktop_app_script])

    def on_quick_caption(ev):
        # Launch studio with active timeline
        disp.ExitLoop()
        py_exe = venv_py if os.path.exists(venv_py) else sys.executable
        subprocess.Popen([py_exe, desktop_app_script])

    win.On.AutoCapWin.Close = on_close
    win.On.CloseBtn.Clicked = on_close
    win.On.LaunchStudioBtn.Clicked = on_launch_studio
    win.On.QuickCaptionBtn.Clicked = on_quick_caption

    win.Show()
    disp.RunLoop()
    win.Hide()

if __name__ == "__main__":
    run_fusion_ui()
