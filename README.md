# ⚡ Auto Caption Studio for DaVinci Resolve Free v21 (and Studio)

A professional, high-performance auto-captioning plugin and drag-and-drop animated title suite built specifically for **DaVinci Resolve Free v21** (and Studio).

---

## 🌟 Why This Plugin is Essential for DaVinci Resolve Free

1. **Bypasses the Studio-Only Paywall**: In DaVinci Resolve, the native "Create Subtitles from Audio" feature is locked behind the paid **DaVinci Resolve Studio** license. This plugin brings fast, 100% free, private, offline speech recognition to the **Free version of DaVinci Resolve v21**.
2. **Animated Drag-and-Drop Styles**: Built-in subtitle tracks in DaVinci Resolve are static and do not support bouncy animations, glowing strokes, or pop-ins. This plugin generates **Text+ Fusion Titles** on regular video tracks with **8 viral animated styles** that you can also drag and drop manually!
3. **Word-Level Precision**: Powered by OpenAI Whisper with millisecond word timestamps for 1-word punchy cuts, 2-3 word dynamic reels, or balanced sentences.

---

## 🎨 8 Drag-and-Drop Styles Included

| Style Name | Description | Best For |
|---|---|---|
| **Hormozi Viral** | Bold gold/yellow text (`#FFE600`), thick black outline, drop shadow, and bouncy scale pop | TikTok, YouTube Shorts, Instagram Reels |
| **TikTok Bounce** | High-contrast pure white text, solid black stroke, and dynamic pop-in | Fast-paced viral social media videos |
| **MrBeast Highlighter** | Electric neon lime-green text (`#39FF14`), heavy comic outline, hard drop shadow | High-energy YouTube videos & challenges |
| **Cinematic Box** | Clean modern typography inside a rounded dark semi-transparent box | Documentaries, Vox-style explainers, tech reviews |
| **Cyber Neon** | Electric cyan text (`#00F5FF`) with dual-layer neon glow & ambient magenta backdrop | Gaming, EDM, tech tutorials, futuristic aesthetic |
| **Clean Minimalist** | Crisp white subtitle with soft diffused ambient shadow | Podcasts, corporate interviews, narrative films |
| **Retro Comic Pop** | Golden yellow text with black border and 3D extruded red shadow offset | Comic reactions, gaming, cartoon commentary |
| **Split Tone** | Vibrant gold-to-white gradient with high-contrast dark border | High-retention talking head videos |

---

## 🚀 How to Use

### Windows First-Time Setup
From the project folder, create the Python environment and install Whisper before installing the Resolve scripts:
```powershell
py -3 -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe installer\install.py
```
If `py` is not available, replace it with the full path to your Python executable.

### Method 1: Using the Desktop Studio App (Recommended)
1. Double-click `AutoCaption.command` on macOS, or run `.\venv\Scripts\python.exe AutoCaption.py` on Windows.
2. The **Auto Caption Studio** window will open.
3. **Select your media**: Click **Browse...** to pick any video/audio file, or click **Fetch from Active Timeline** to auto-load media from DaVinci Resolve.
4. **Choose your style**: Select any of the 8 presets (e.g., *Hormozi Viral*, *TikTok Bounce*, *Cinematic Box*).
5. **Set timing & layout**:
   - **1_word**: 1 word per clip (ultra fast-paced).
   - **short**: 2–3 words per clip (the TikTok/Shorts sweet spot).
   - **balanced**: 4–6 words per clip (classic YouTube).
   - **sentence**: Natural full sentences.
6. Click **🚀 Transcribe & Generate Captions**.
7. Preview or edit any words in the interactive table.
8. Click **🎬 Send to DaVinci Timeline** (or **💾 Export FCPXML** / **📄 Export SRT**).
   - DaVinci Resolve will automatically import a timeline populated with your styled Text+ clips aligned to the audio!

---

### Method 2: Directly Inside DaVinci Resolve
1. Open DaVinci Resolve.
2. In the top menu, go to:
   **Workspace > Scripts > Utility > AutoCaption**
3. The Auto Caption panel opens in Resolve. It reads the active timeline and refreshes the live timeline connection while open.
4. If `AutoCaption` is not listed, install or update the scripts with `.\venv\Scripts\python.exe installer\install.py`, then restart Resolve.

---

### Method 3: Drag & Drop Styles from the Effects Library
1. In DaVinci Resolve, switch to the **Edit** page.
2. Open the **Effects Library** (top left).
3. Expand **Titles > Auto Captions**.
4. You will see all 8 custom styles:
   - `Hormozi Viral`
   - `TikTok Bounce`
   - `MrBeast Highlighter`
   - `Cinematic Box`
   - `Cyber Neon`
   - `Clean Minimalist`
   - `Retro Comic Pop`
   - `Split Tone`
5. Simply **drag and drop** any style directly onto a video track above your clips!
6. In the **Inspector** (top right), easily adjust text, font, size, colors, or tracking.

---

## 📁 Installation & File Locations

The installation script (`installer/install.py`) automatically placed all files into DaVinci Resolve's active directories:

- **Fusion Templates (.setting & .drfx)**:
  `~/Library/Application Support/Blackmagic Design/DaVinci Resolve/Fusion/Templates/Edit/Titles/Auto Captions/`
- **Resolve Script Menu**:
  `~/Library/Application Support/Blackmagic Design/DaVinci Resolve/Fusion/Scripts/Utility/AutoCaption.py`

To re-install or update anytime:
```bash
python3 installer/install.py
```

---

## 🛠️ Requirements & Performance
- **DaVinci Resolve**: Free v21+ or Studio v21+
- **macOS**: Apple Silicon (M1/M2/M3/M4) or Intel
- **Whisper Models**:
  - `base` (Default, recommended — transcribes 1 minute of audio in ~2-3 seconds on M-series chips)
  - `tiny` (Fastest, ~10x realtime)
  - `small` / `medium` (High accuracy multilingual)
