"""
Auto Caption for DaVinci Resolve Free v21 - Modern Desktop GUI
"""

import os
import sys
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import List, Optional

# Add parent directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.styles import STYLES, get_style
from core.transcriber import CaptionTranscriber, CaptionSegment, export_srt, export_json
from core.xml_generator import generate_fcpxml, generate_fcp7_xml
from core.timeline_injector import ResolveBridge

class AutoCaptionApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Auto Caption Studio — DaVinci Resolve v21 (Free & Studio)")
        self.geometry("960x720")
        self.minsize(860, 640)
        self.configure(bg="#141418")

        self.bridge = ResolveBridge()
        self.segments: List[CaptionSegment] = []
        self.input_file_path = tk.StringVar()
        self.selected_style = tk.StringVar(value="Hormozi Viral")
        self.selected_model = tk.StringVar(value="base")
        self.selected_language = tk.StringVar(value="Auto")
        self.selected_chunk = tk.StringVar(value="short")
        self.selected_case = tk.StringVar(value="UPPERCASE")
        self.status_text = tk.StringVar(value="Ready. Select a video or audio file to begin.")
        self.progress_value = tk.DoubleVar(value=0.0)

        self.is_pinned = tk.BooleanVar(value=True)
        self.attributes("-topmost", True)  # Float on top of DaVinci Resolve like an integrated panel
        self.is_compact = False

        self._setup_styles()
        self._build_ui()
        self._check_resolve_connection()

    def _toggle_pin(self):
        pinned = self.is_pinned.get()
        self.attributes("-topmost", pinned)
        self.pin_btn.config(text="📌 Pinned (Floating Panel)" if pinned else "📍 Unpinned")

    def _toggle_compact(self):
        self.is_compact = not self.is_compact
        if self.is_compact:
            self.main_paned.forget(self.right_card)
            self.geometry("420x720")
            self.compact_btn.config(text="⇲ Expand Studio")
            self.title("Auto Caption — Floating Side Panel")
        else:
            self.main_paned.add(self.right_card, weight=2)
            self.geometry("960x720")
            self.compact_btn.config(text="⇱ Compact Panel")
            self.title("Auto Caption Studio — DaVinci Resolve v21 (Free & Studio)")

    def _setup_styles(self):
        self.style = ttk.Style(self)
        self.style.theme_use("clam")

        # Configure Dark Palette
        self.style.configure(".", background="#141418", foreground="#E0E0E6", font=("Helvetica", 11))
        self.style.configure("TFrame", background="#141418")
        self.style.configure("Card.TFrame", background="#1F1F27", relief="flat")
        self.style.configure("Header.TLabel", font=("Helvetica", 16, "bold"), foreground="#FFFFFF", background="#141418")
        self.style.configure("SubHeader.TLabel", font=("Helvetica", 10), foreground="#8E8E9F", background="#141418")
        self.style.configure("Section.TLabel", font=("Helvetica", 12, "bold"), foreground="#F3A63B", background="#1F1F27")
        self.style.configure("Muted.TLabel", font=("Helvetica", 10), foreground="#9E9EAF", background="#1F1F27")

        # Buttons
        self.style.configure("Accent.TButton", font=("Helvetica", 11, "bold"), background="#E58B20", foreground="#FFFFFF", padding=(12, 6))
        self.style.map("Accent.TButton", background=[("active", "#F39C38"), ("disabled", "#554433")])

        self.style.configure("Success.TButton", font=("Helvetica", 11, "bold"), background="#10B981", foreground="#FFFFFF", padding=(12, 6))
        self.style.map("Success.TButton", background=[("active", "#059669")])

        self.style.configure("Secondary.TButton", font=("Helvetica", 10), background="#2E2E3A", foreground="#E0E0E6", padding=(8, 4))
        self.style.map("Secondary.TButton", background=[("active", "#3E3E4E")])

        # Treeview (Captions Table)
        self.style.configure("Treeview",
                             background="#181820",
                             foreground="#E0E0E6",
                             fieldbackground="#181820",
                             rowheight=26,
                             font=("Helvetica", 10))
        self.style.configure("Treeview.Heading",
                             background="#282834",
                             foreground="#F0F0F8",
                             font=("Helvetica", 10, "bold"))
        self.style.map("Treeview", background=[("selected", "#E58B20")], foreground=[("selected", "#FFFFFF")])

        # Combobox
        self.style.configure("TCombobox", fieldbackground="#282834", background="#282834", foreground="#FFFFFF")

    def _build_ui(self):
        # Top Header Bar
        header_frame = ttk.Frame(self)
        header_frame.pack(fill="x", padx=20, pady=(15, 10))

        title_box = ttk.Frame(header_frame)
        title_box.pack(side="left")
        ttk.Label(title_box, text="⚡ Auto Caption Studio", style="Header.TLabel").pack(anchor="w")
        ttk.Label(title_box, text="DaVinci Resolve Free v21 Plugin & Drag-and-Drop Caption Generator", style="SubHeader.TLabel").pack(anchor="w")

        controls_box = ttk.Frame(header_frame)
        controls_box.pack(side="right")

        self.pin_btn = tk.Checkbutton(
            controls_box, text="📌 Float Panel", variable=self.is_pinned, command=self._toggle_pin,
            bg="#2A2A38", fg="#F59E0B", selectcolor="#1E1E28", activebackground="#2A2A38",
            activeforeground="#F59E0B", padx=6, pady=2, relief="flat", font=("Helvetica", 10, "bold")
        )
        self.pin_btn.pack(side="left", padx=4)

        self.compact_btn = ttk.Button(controls_box, text="⇱ Compact Side Panel", style="Secondary.TButton", command=self._toggle_compact)
        self.compact_btn.pack(side="left", padx=4)

        self.badge_label = tk.Label(controls_box, text="Checking Resolve...", font=("Helvetica", 10, "bold"),
                                    bg="#2A2A38", fg="#9E9EAF", padx=8, pady=4)
        self.badge_label.pack(side="left", padx=4)

        # Main Layout: 2 Columns (Left Settings & Controls, Right Preview & Table)
        self.main_paned = ttk.PanedWindow(self, orient="horizontal")
        self.main_paned.pack(fill="both", expand=True, padx=20, pady=10)

        # Left Column: Configuration Card
        left_card = ttk.Frame(self.main_paned, style="Card.TFrame", padding=15)
        self.main_paned.add(left_card, weight=1)

        # 1. Media Input Section
        ttk.Label(left_card, text="1. Select Media File", style="Section.TLabel").pack(anchor="w", pady=(0, 6))
        file_row = ttk.Frame(left_card, style="Card.TFrame")
        file_row.pack(fill="x", pady=(0, 15))
        self.file_entry = tk.Entry(file_row, textvariable=self.input_file_path, bg="#282834", fg="#FFFFFF",
                                   insertbackground="#FFFFFF", relief="flat", font=("Helvetica", 10))
        self.file_entry.pack(side="left", fill="x", expand=True, ipady=4, padx=(0, 6))
        ttk.Button(file_row, text="Browse...", style="Secondary.TButton", command=self._browse_file).pack(side="right")

        # Timeline Media Auto-Detect Button (if connected)
        self.detect_btn = ttk.Button(left_card, text="🎯 Fetch from Active Timeline", style="Secondary.TButton",
                                     command=self._fetch_from_timeline)
        self.detect_btn.pack(fill="x", pady=(0, 15))

        # 2. Style Preset Picker
        ttk.Label(left_card, text="2. Drag-and-Drop Style Preset", style="Section.TLabel").pack(anchor="w", pady=(0, 6))
        style_cb = ttk.Combobox(left_card, textvariable=self.selected_style, values=list(STYLES.keys()), state="readonly")
        style_cb.pack(fill="x", pady=(0, 4))
        style_cb.bind("<<ComboboxSelected>>", self._on_style_changed)

        self.style_desc_lbl = ttk.Label(left_card, text=STYLES["Hormozi Viral"]["description"],
                                        style="Muted.TLabel", wraplength=300)
        self.style_desc_lbl.pack(anchor="w", pady=(0, 15))

        # 3. Caption Chunking & Casing
        ttk.Label(left_card, text="3. Caption Timing & Layout", style="Section.TLabel").pack(anchor="w", pady=(0, 6))
        
        chunk_frame = ttk.Frame(left_card, style="Card.TFrame")
        chunk_frame.pack(fill="x", pady=(0, 8))
        ttk.Label(chunk_frame, text="Words per Clip:", style="Muted.TLabel").pack(side="left")
        chunk_cb = ttk.Combobox(chunk_frame, textvariable=self.selected_chunk, width=15, state="readonly",
                                values=["1_word", "short", "balanced", "sentence"])
        chunk_cb.pack(side="right")

        case_frame = ttk.Frame(left_card, style="Card.TFrame")
        case_frame.pack(fill="x", pady=(0, 15))
        ttk.Label(case_frame, text="Text Casing:", style="Muted.TLabel").pack(side="left")
        case_cb = ttk.Combobox(case_frame, textvariable=self.selected_case, width=15, state="readonly",
                               values=["UPPERCASE", "Title Case", "Original"])
        case_cb.pack(side="right")

        # 4. Whisper AI Model & Language
        ttk.Label(left_card, text="4. Speech Recognition AI", style="Section.TLabel").pack(anchor="w", pady=(0, 6))
        model_frame = ttk.Frame(left_card, style="Card.TFrame")
        model_frame.pack(fill="x", pady=(0, 8))
        ttk.Label(model_frame, text="Model:", style="Muted.TLabel").pack(side="left")
        model_cb = ttk.Combobox(model_frame, textvariable=self.selected_model, width=15, state="readonly",
                                values=["tiny", "base", "small", "medium"])
        model_cb.pack(side="right")

        lang_frame = ttk.Frame(left_card, style="Card.TFrame")
        lang_frame.pack(fill="x", pady=(0, 20))
        ttk.Label(lang_frame, text="Language:", style="Muted.TLabel").pack(side="left")
        lang_cb = ttk.Combobox(lang_frame, textvariable=self.selected_language, width=15, state="readonly",
                              values=["Auto", "en", "es", "fr", "de", "it", "pt", "ja", "zh", "hi", "si"])
        lang_cb.pack(side="right")

        # Transcribe Action Button
        self.transcribe_btn = ttk.Button(left_card, text="🚀 Transcribe & Generate Captions", style="Accent.TButton",
                                         command=self._start_transcription)
        self.transcribe_btn.pack(fill="x", ipady=4, pady=(0, 10))

        # Install Templates Button
        ttk.Button(left_card, text="📦 Install Styles into DaVinci Titles", style="Secondary.TButton",
                   command=self._install_templates_action).pack(fill="x")

        # Right Column: Captions Preview Table & Export Actions
        self.right_card = ttk.Frame(self.main_paned, style="Card.TFrame", padding=15)
        self.main_paned.add(self.right_card, weight=2)

        right_header = ttk.Frame(self.right_card, style="Card.TFrame")
        right_header.pack(fill="x", pady=(0, 10))
        ttk.Label(right_header, text="Generated Captions Preview", style="Section.TLabel").pack(side="left")
        self.count_label = ttk.Label(right_header, text="0 clips", style="Muted.TLabel")
        self.count_label.pack(side="right")

        # Captions Treeview Table
        tree_frame = ttk.Frame(self.right_card, style="Card.TFrame")
        tree_frame.pack(fill="both", expand=True, pady=(0, 10))

        columns = ("#", "Start", "End", "Duration", "Caption Text")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", selectmode="browse")
        self.tree.heading("#", text="#")
        self.tree.heading("Start", text="Start")
        self.tree.heading("End", text="End")
        self.tree.heading("Duration", text="Dur")
        self.tree.heading("Caption Text", text="Caption Text")

        self.tree.column("#", width=40, anchor="center")
        self.tree.column("Start", width=70, anchor="center")
        self.tree.column("End", width=70, anchor="center")
        self.tree.column("Duration", width=60, anchor="center")
        self.tree.column("Caption Text", width=320, anchor="w")

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.tree.bind("<Double-1>", self._on_edit_caption)

        # Export & Direct Import Action Bar
        action_bar = ttk.Frame(self.right_card, style="Card.TFrame")
        action_bar.pack(fill="x", pady=(5, 0))

        self.import_btn = ttk.Button(action_bar, text="🎬 Send to DaVinci Timeline", style="Success.TButton",
                                     command=self._send_to_resolve)
        self.import_btn.pack(side="left", padx=(0, 8), fill="x", expand=True)

        ttk.Button(action_bar, text="💾 Export FCPXML", style="Secondary.TButton",
                   command=self._export_fcpxml).pack(side="left", padx=(0, 6))
        ttk.Button(action_bar, text="📄 Export SRT", style="Secondary.TButton",
                   command=self._export_srt).pack(side="left")

        # Bottom Status & Progress Bar
        bottom_bar = ttk.Frame(self)
        bottom_bar.pack(fill="x", side="bottom", padx=20, pady=(0, 10))

        self.progress_bar = ttk.Progressbar(bottom_bar, variable=self.progress_value, maximum=1.0)
        self.progress_bar.pack(fill="x", pady=(0, 4))
        self.status_lbl = ttk.Label(bottom_bar, textvariable=self.status_text, style="SubHeader.TLabel")
        self.status_lbl.pack(anchor="w")

    def _check_resolve_connection(self):
        connected = self.bridge.is_connected()
        if connected:
            proj = self.bridge.get_current_project()
            proj_name = proj.GetName() if proj else "No Project Open"
            self.badge_label.config(text=f"🟢 Connected: {proj_name}", bg="#064E3B", fg="#6EE7B7")
            self.import_btn.config(state="normal")
        else:
            self.badge_label.config(text="⚪ DaVinci Resolve Not Detected (Export Available)", bg="#2A2A38", fg="#9E9EAF")

    def _on_style_changed(self, event=None):
        name = self.selected_style.get()
        style = get_style(name)
        self.style_desc_lbl.config(text=style["description"])
        if "default_chunk" in style:
            self.selected_chunk.set(style["default_chunk"])
        if "default_case" in style:
            self.selected_case.set(style["default_case"])

    def _browse_file(self):
        file_path = filedialog.askopenfilename(
            title="Select Video or Audio File",
            filetypes=[("Media Files", "*.mp4 *.mov *.mkv *.mp3 *.wav *.m4a *.aac *.flac *.avi"), ("All Files", "*.*")]
        )
        if file_path:
            self.input_file_path.set(file_path)

    def _fetch_from_timeline(self):
        info = self.bridge.get_timeline_info()
        source_files = info.get("source_files", [])
        if source_files:
            self.input_file_path.set(source_files[0])
            self.status_text.set(f"Loaded media from timeline: {os.path.basename(source_files[0])}")
        else:
            messagebox.showinfo("Timeline Media", "No media files found on active timeline. Please select a video file manually.")

    def _start_transcription(self):
        media_path = self.input_file_path.get().strip()
        if not media_path or not os.path.exists(media_path):
            messagebox.showwarning("File Missing", "Please select a valid media file first!")
            return

        self.transcribe_btn.config(state="disabled")
        self.progress_value.set(0.0)
        self.status_text.set("Initializing speech recognition...")

        model = self.selected_model.get()
        lang = self.selected_language.get()
        chunk = self.selected_chunk.get()
        casing = self.selected_case.get()

        def worker():
            try:
                def progress_cb(msg, val):
                    self.after(0, lambda: self._update_progress(msg, val))

                transcriber = CaptionTranscriber(model_size=model, language=lang)
                segments = transcriber.transcribe(
                    media_path=media_path,
                    chunk_mode=chunk,
                    casing=casing,
                    progress_callback=progress_cb
                )
                self.after(0, lambda: self._on_transcription_success(segments))
            except Exception as e:
                self.after(0, lambda: self._on_transcription_error(str(e)))

        threading.Thread(target=worker, daemon=True).start()

    def _update_progress(self, msg: str, val: float):
        self.status_text.set(msg)
        self.progress_value.set(val)

    def _on_transcription_success(self, segments: List[CaptionSegment]):
        self.segments = segments
        self.transcribe_btn.config(state="normal")
        self.status_text.set(f"Transcription complete! Created {len(segments)} caption clips.")
        self.count_label.config(text=f"{len(segments)} clips")

        # Populate tree
        for row in self.tree.get_children():
            self.tree.delete(row)

        for s in segments:
            dur = f"{s.end_time - s.start_time:.2f}s"
            start_str = f"{s.start_time:.2f}s"
            end_str = f"{s.end_time:.2f}s"
            self.tree.insert("", "end", values=(s.index, start_str, end_str, dur, s.text))

    def _on_transcription_error(self, err_msg: str):
        self.transcribe_btn.config(state="normal")
        self.status_text.set(f"Error: {err_msg}")
        messagebox.showerror("Transcription Error", f"Transcription failed:\n{err_msg}")

    def _on_edit_caption(self, event):
        selected_item = self.tree.selection()
        if not selected_item:
            return
        item_vals = self.tree.item(selected_item[0], "values")
        idx = int(item_vals[0]) - 1
        current_text = item_vals[4]

        # Simple prompt dialog
        edit_win = tk.Toplevel(self)
        edit_win.title(f"Edit Caption #{idx + 1}")
        edit_win.geometry("400, 140")
        edit_win.configure(bg="#1E1E24")
        edit_win.transient(self)
        edit_win.grab_set()

        ttk.Label(edit_win, text=f"Edit Text ({item_vals[1]} - {item_vals[2]}):", style="Section.TLabel").pack(padx=15, pady=(15, 6), anchor="w")
        txt_var = tk.StringVar(value=current_text)
        entry = tk.Entry(edit_win, textvariable=txt_var, font=("Helvetica", 11), bg="#282834", fg="#FFFFFF", relief="flat")
        entry.pack(fill="x", padx=15, pady=6, ipady=4)
        entry.focus_set()

        def save():
            new_val = txt_var.get().strip()
            if new_val and idx < len(self.segments):
                self.segments[idx].text = new_val
                new_vals = list(item_vals)
                new_vals[4] = new_val
                self.tree.item(selected_item[0], values=new_vals)
            edit_win.destroy()

        btn_box = ttk.Frame(edit_win, style="Card.TFrame")
        btn_box.pack(fill="x", padx=15, pady=(5, 10))
        ttk.Button(btn_box, text="Save", style="Accent.TButton", command=save).pack(side="right")
        ttk.Button(btn_box, text="Cancel", style="Secondary.TButton", command=edit_win.destroy).pack(side="right", padx=6)

    def _send_to_resolve(self):
        if not self.segments:
            messagebox.showwarning("No Captions", "Please transcribe media first!")
            return

        # Generate temporary FCPXML file
        import tempfile
        style_name = self.selected_style.get()
        tmp_dir = tempfile.gettempdir()
        xml_path = os.path.join(tmp_dir, f"AutoCaptions_{style_name.replace(' ', '_')}.fcpxml")

        generate_fcpxml(
            segments=self.segments,
            output_path=xml_path,
            fps=30.0,
            style_name=style_name,
            timeline_name=f"Captions_{style_name}"
        )

        # Check bridge
        if not self.bridge.is_connected():
            # Prompt user to import the generated file
            messagebox.showinfo(
                "Exported XML",
                f"DaVinci Resolve is not actively connected via API.\n\n"
                f"FCPXML has been saved to:\n{xml_path}\n\n"
                f"In DaVinci Resolve Free v21:\nGo to File > Import > Timeline... and select this file!"
            )
            return

        success = self.bridge.import_timeline_xml(xml_path)
        if success:
            messagebox.showinfo("Success", f"Captions timeline imported successfully into DaVinci Resolve!\nStyle: {style_name}")
            self.status_text.set("Captions timeline successfully sent to DaVinci Resolve!")
        else:
            messagebox.showwarning("Import Note", f"Automatic import could not be completed directly.\nYou can import the generated XML manually:\n{xml_path}")

    def _export_fcpxml(self):
        if not self.segments:
            messagebox.showwarning("No Captions", "Please transcribe media first!")
            return
        save_path = filedialog.asksaveasfilename(
            title="Save FCPXML Timeline",
            defaultextension=".fcpxml",
            filetypes=[("FCPXML Files", "*.fcpxml"), ("All Files", "*.*")]
        )
        if save_path:
            generate_fcpxml(
                segments=self.segments,
                output_path=save_path,
                style_name=self.selected_style.get()
            )
            messagebox.showinfo("Saved", f"FCPXML timeline saved:\n{save_path}")

    def _export_srt(self):
        if not self.segments:
            messagebox.showwarning("No Captions", "Please transcribe media first!")
            return
        save_path = filedialog.asksaveasfilename(
            title="Save Subtitle File",
            defaultextension=".srt",
            filetypes=[("SRT Subtitles", "*.srt"), ("All Files", "*.*")]
        )
        if save_path:
            style = get_style(self.selected_style.get())
            export_srt(self.segments, save_path, color_hex=style.get("color_hex"))
            messagebox.showinfo("Saved", f"SRT subtitle file saved:\n{save_path}")

    def _install_templates_action(self):
        from installer.install import install_all
        res = install_all()
        if res.get("success"):
            messagebox.showinfo("Installed", "Styles and scripts successfully installed into DaVinci Resolve 21!\n\nYou can now drag and drop them from Effects > Titles > Auto Captions.")
        else:
            messagebox.showerror("Install Error", f"Installation encountered an issue:\n{res.get('error')}")

def main():
    app = AutoCaptionApp()
    app.mainloop()

if __name__ == "__main__":
    main()
