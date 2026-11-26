"""
Native DaVinci Resolve Qt Panel Window using built-in UIManager
Appears directly INSIDE DaVinci Resolve under Workspace > Scripts > Utility > AutoCaption
"""

import os
import sys
import tempfile
import threading

def run_fusion_ui(fusion_app=None, scripting_module=None, resolve_app=None):
    fu = fusion_app
    bmd = scripting_module
    resolve = resolve_app

    if not fu or not bmd or not resolve:
        print("[AutoCaption] Error: This script must be run inside DaVinci Resolve.")
        return

    ui = fu.UIManager
    dispatcher = bmd.UIDispatcher(ui)

    winID = "com.autocaption.resolve.PanelWindow"
    existing_win = ui.FindWindow(winID)
    if existing_win:
        existing_win.Show()
        existing_win.Raise()
        return

    # Project directories
    project_dir = os.environ.get(
        "AUTO_CAPTION_PROJECT_DIR",
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    )
    if sys.platform.startswith("win"):
        venv_py = os.path.join(project_dir, "venv", "Scripts", "python.exe")
    else:
        venv_py = os.path.join(project_dir, "venv", "bin", "python3")
    quick_caption_cli = os.path.join(project_dir, "core", "quick_caption.py")

    # Detect current project and timeline
    pm = resolve.GetProjectManager()
    proj = pm.GetCurrentProject() if pm else None
    timeline = proj.GetCurrentTimeline() if proj else None

    timeline_name = timeline.GetName() if timeline else "No Timeline Open"
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

    active_file = found_media[0] if found_media else ""
    file_display = os.path.basename(active_file) if active_file else "No media clips detected on timeline"

    # Style presets
    styles = [
        "Hormozi Viral",
        "TikTok Bounce",
        "MrBeast Highlighter",
        "Cinematic Box",
        "Cyber Neon",
        "Clean Minimalist",
        "Retro Comic Pop",
        "Split Tone"
    ]

    header_html = """
    <html><body>
    <table width="100%" cellpadding="0" cellspacing="0">
      <tr>
        <td>
          <h2 style="color:#F3A63B; margin:0; padding:0;">⚡ Auto Caption Studio</h2>
          <p style="color:#A0A0B0; margin:2px 0 0 0; font-size:11px;">DaVinci Resolve Free v21 Auto-Subtitle & Animated Title Panel</p>
        </td>
      </tr>
    </table>
    </body></html>
    """

    win = dispatcher.AddWindow({
        'ID': winID,
        'Geometry': [ 250, 180, 560, 540 ],
        'WindowTitle': "⚡ Auto Caption Studio — DaVinci Resolve",
    },
    ui.VGroup({ 'Spacing': 8, 'Margin': 15 }, [
        ui.Label({ 'Text': header_html, 'Weight': 0 }),
        ui.VGap(2),

        # Section 1: Active Timeline & Media
        ui.Label({ 'Text': '<b>1. Timeline Source Audio</b>', 'Weight': 0 }),
        ui.HGroup({ 'Weight': 0 }, [
            ui.LineEdit({ 'ID': 'FileBox', 'Text': active_file, 'PlaceholderText': 'Click Browse or fetch from timeline...', 'ReadOnly': True, 'Weight': 0.8 }),
            ui.Button({ 'ID': 'BrowseBtn', 'Text': 'Browse...', 'Weight': 0.2 }),
        ]),
        ui.Label({ 'ID': 'TimelineStatus', 'Text': f'<small style="color:#10B981;">● Active Timeline: {timeline_name} ({len(found_media)} media clips detected)</small>', 'Weight': 0 }),
        ui.VGap(4),

        # Section 2: Style Preset Picker
        ui.Label({ 'Text': '<b>2. Select Caption Style (Drag-and-Drop Preset)</b>', 'Weight': 0 }),
        ui.ComboBox({ 'ID': 'StyleCombo', 'Weight': 0 }),
        ui.Label({ 'ID': 'StyleDesc', 'Text': '<small style="color:#A0A0B0;">Bold yellow viral text with thick black outline, drop shadow, and pop bounce</small>', 'Weight': 0 }),
        ui.VGap(4),

        # Section 3: Timing & Layout
        ui.Label({ 'Text': '<b>3. Caption Timing & Length</b>', 'Weight': 0 }),
        ui.HGroup({ 'Weight': 0 }, [
            ui.VGroup({ 'Weight': 0.5 }, [
                ui.Label({ 'Text': '<small>Words per Clip:</small>', 'Weight': 0 }),
                ui.ComboBox({ 'ID': 'ChunkCombo', 'Weight': 0 }),
            ]),
            ui.VGroup({ 'Weight': 0.5 }, [
                ui.Label({ 'Text': '<small>Whisper AI Model:</small>', 'Weight': 0 }),
                ui.ComboBox({ 'ID': 'ModelCombo', 'Weight': 0 }),
            ]),
        ]),
        ui.VGap(8),

        # Progress / Status Box
        ui.Label({ 'ID': 'StatusMsg', 'Text': '<span style="color:#E0E0E6;">Ready. Click Auto-Caption to transcribe timeline speech.</span>', 'Weight': 0 }),
        ui.Timer({ 'ID': 'LiveTimelineTimer', 'Interval': 3000, 'SingleShot': False }),

        # Action Buttons
        ui.VGap(4),
        ui.Button({ 'ID': 'ActionBtn', 'Text': '⚡ AUTO-CAPTION TIMELINE NOW', 'Weight': 0 }),
        ui.Button({ 'ID': 'CloseBtn', 'Text': 'Close Panel', 'Weight': 0 }),
    ]))

    items = win.GetItems()

    # Populate ComboBoxes
    for s in styles:
        items['StyleCombo'].AddItem(s)

    chunks = [
        "short (2-3 words, TikTok/Reels)",
        "1_word (Punchy)",
        "balanced (4-6 words)",
        "sentence (Full Sentences)"
    ]
    for c in chunks:
        items['ChunkCombo'].AddItem(c)

    for m in ["base (Recommended - Fast & Accurate)", "tiny (Fastest)", "small (High Accuracy)"]:
        items['ModelCombo'].AddItem(m)

    # Style description mapping
    style_descs = {
        "Hormozi Viral": "Bold yellow viral text with thick black outline, drop shadow, and pop bounce",
        "TikTok Bounce": "High contrast white text with solid black stroke and dynamic bounce pop",
        "MrBeast Highlighter": "Electric neon lime-green text with heavy comic outline and hard drop shadow",
        "Cinematic Box": "Clean modern sans-serif typography inside a rounded dark translucent box",
        "Cyber Neon": "Futuristic electric cyan with dual glowing outline and ambient magenta backlight",
        "Clean Minimalist": "Crisp white subtitle with soft diffused ambient shadow for interviews",
        "Retro Comic Pop": "Golden yellow text with black border and 3D extruded red shadow offset",
        "Split Tone": "Gold-to-white gradient with high-contrast dark border"
    }

    # Event Handlers
    def on_close(ev):
        dispatcher.ExitLoop()

    def on_style_changed(ev):
        idx = items['StyleCombo'].CurrentIndex
        if 0 <= idx < len(styles):
            desc = style_descs.get(styles[idx], "")
            items['StyleDesc'].Text = f'<small style="color:#A0A0B0;">{desc}</small>'

    def on_browse(ev):
        chosen = fu.RequestFile()
        if chosen:
            items['FileBox'].Text = str(chosen)
            items['TimelineStatus'].Text = f'<small style="color:#10B981;">● Selected file: {os.path.basename(str(chosen))}</small>'

    def refresh_live_timeline(ev):
        pm = resolve.GetProjectManager()
        live_project = pm.GetCurrentProject() if pm else None
        live_timeline = live_project.GetCurrentTimeline() if live_project else None
        if not live_timeline:
            items['TimelineStatus'].Text = '<small style="color:#9E9EAF;">● Resolve live connection ready - no timeline open</small>'
            return

        live_media = []
        for t_type in ["video", "audio"]:
            count = live_timeline.GetTrackCount(t_type)
            for idx in range(1, count + 1):
                for item in live_timeline.GetItemListInTrack(t_type, idx) or []:
                    mp_item = item.GetMediaPoolItem()
                    if mp_item:
                        fp = mp_item.GetClipProperty().get("File Path", "")
                        if fp and os.path.exists(fp) and fp not in live_media:
                            live_media.append(fp)

        status = f'<small style="color:#10B981;">● Live Timeline: {live_timeline.GetName()}'
        status += f" ({len(live_media)} media clips detected)</small>"
        items['TimelineStatus'].Text = status
        if live_media:
            current = items['FileBox'].Text.strip()
            if not current or not os.path.exists(current):
                items['FileBox'].Text = live_media[0]

    def on_run_caption(ev):
        if not os.path.isfile(venv_py):
            items['StatusMsg'].Text = (
                '<span style="color:#EF4444;">Whisper is not installed. Run the setup commands '
                'from the project README, then reopen this panel.</span>'
            )
            return

        target_media = items['FileBox'].Text.strip()
        if not target_media or not os.path.exists(target_media):
            items['StatusMsg'].Text = '<span style="color:#EF4444;">Please select a media file or open a timeline with clips first!</span>'
            return

        style_idx = items['StyleCombo'].CurrentIndex
        chosen_style = styles[style_idx] if 0 <= style_idx < len(styles) else "Hormozi Viral"

        chunk_raw = items['ChunkCombo'].CurrentText
        chunk_mode = "short"
        if "1_word" in chunk_raw:
            chunk_mode = "1_word"
        elif "balanced" in chunk_raw:
            chunk_mode = "balanced"
        elif "sentence" in chunk_raw:
            chunk_mode = "sentence"

        model_raw = items['ModelCombo'].CurrentText
        model_name = "base"
        if "tiny" in model_raw:
            model_name = "tiny"
        elif "small" in model_raw:
            model_name = "small"

        items['StatusMsg'].Text = '<span style="color:#F3A63B;">⏳ Transcribing speech and creating captions... Please wait.</span>'
        items['ActionBtn'].Enabled = False

        def bg_worker():
            try:
                cmd = [
                    venv_py, quick_caption_cli,
                    "--media", target_media,
                    "--style", chosen_style,
                    "--chunk", chunk_mode,
                    "--model", model_name,
                ]
                proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                
                # Check for output FCPXML in Movies
                safe_style = chosen_style.replace(" ", "_")
                xml_path = os.path.expanduser(f"~/Movies/Captions_{safe_style}.fcpxml")

                if os.path.exists(xml_path):
                    # Automatically import into DaVinci Resolve!
                    mp = proj.GetMediaPool() if proj else None
                    imported = False
                    if mp:
                        imported = mp.ImportTimelineFromFile(xml_path, {"importSourceClips": False})
                    
                    if imported:
                        items['StatusMsg'].Text = f'<span style="color:#10B981;"><b>✓ Success!</b> Imported Captions timeline with <b>{chosen_style}</b> style!</span>'
                    else:
                        items['StatusMsg'].Text = f'<span style="color:#10B981;"><b>✓ Captions Ready!</b> Saved to Movies/{os.path.basename(xml_path)}. Drag it into Resolve!</span>'
                else:
                    items['StatusMsg'].Text = f'<span style="color:#EF4444;">Transcription error: {proc.stderr[:100]}</span>'
            except Exception as ex:
                items['StatusMsg'].Text = f'<span style="color:#EF4444;">Error: {str(ex)}</span>'
            finally:
                items['ActionBtn'].Enabled = True

        threading.Thread(target=bg_worker, daemon=True).start()

    # Bind handlers
    win.On[winID].Close = on_close
    win.On['CloseBtn'].Clicked = on_close
    win.On['StyleCombo'].CurrentIndexChanged = on_style_changed
    win.On['BrowseBtn'].Clicked = on_browse
    win.On['ActionBtn'].Clicked = on_run_caption
    win.On['LiveTimelineTimer'].Timer = refresh_live_timeline

    win.Show()
    try:
        items['LiveTimelineTimer'].Start()
    except Exception:
        pass
    dispatcher.RunLoop()
    win.Hide()

if __name__ == "__main__":
    run_fusion_ui()
