#!/usr/bin/env python3
"""
Automated Installer for DaVinci Resolve Auto Caption Plugin & Style Templates
Supports DaVinci Resolve Free & Studio v21 on macOS, Windows, and Linux.
"""

import os
import sys
import shutil
import zipfile

def get_resolve_support_paths():
    """Returns the platform-specific support paths for DaVinci Resolve."""
    home = os.path.expanduser("~")
    
    if sys.platform == "darwin":
        base = os.path.join(home, "Library", "Application Support", "Blackmagic Design", "DaVinci Resolve")
    elif sys.platform.startswith("win"):
        appdata = os.getenv("APPDATA", os.path.join(home, "AppData", "Roaming"))
        base = os.path.join(appdata, "Blackmagic Design", "DaVinci Resolve", "Support")
    else:  # linux
        base = os.path.join(home, ".local", "share", "DaVinciResolve")

    return {
        "templates_titles": os.path.join(base, "Fusion", "Templates", "Edit", "Titles"),
        "scripts_utility": os.path.join(base, "Fusion", "Scripts", "Utility"),
        "scripts_edit": os.path.join(base, "Fusion", "Scripts", "Edit"),
    }


def _lua_quote(value):
    escaped = str(value).replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
    return f'"{escaped}"'


def install_all():
    """Installs template styles and scripts into DaVinci Resolve directories."""
    paths = get_resolve_support_paths()
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if base_dir not in sys.path:
        sys.path.insert(0, base_dir)
    from build_templates import main as generate_templates
    from core.styles import STYLES

    generate_templates()

    templates_src = os.path.join(base_dir, "templates")
    drfx_src = os.path.join(base_dir, "dist", "AutoCaptions.drfx")

    # 1. Install .setting files to Templates/Edit/Titles/Auto Captions
    target_titles_dir = os.path.join(paths["templates_titles"], "Auto Captions")
    os.makedirs(target_titles_dir, exist_ok=True)

    installed_templates = []
    if os.path.exists(templates_src):
        for f in os.listdir(templates_src):
            if f.endswith(".setting"):
                src_file = os.path.join(templates_src, f)
                dst_file = os.path.join(target_titles_dir, f)
                shutil.copy2(src_file, dst_file)
                installed_templates.append(f)

    # 2. Install .drfx bundle
    if os.path.exists(drfx_src):
        dst_drfx = os.path.join(paths["templates_titles"], "AutoCaptions.drfx")
        shutil.copy2(drfx_src, dst_drfx)

    # 3. Install the native Fusion UI script in the Utility menu.
    script_folder = paths["scripts_utility"]
    os.makedirs(script_folder, exist_ok=True)
    script_entry = os.path.join(base_dir, "AutoCaption.lua")
    target_script = os.path.join(script_folder, "AutoCaption.lua")
    lua_styles = ",\n".join(
        "    { name = %s, description = %s, fill = %s, stroke = %s, kind = %s, background = %s }" % (
            _lua_quote(style["name"]),
            _lua_quote(style["description"]),
            _lua_quote(style.get("color_hex", "#FFFFFF")),
            _lua_quote(style.get("stroke_hex") or "#000000"),
            _lua_quote(style.get("preview_kind", "pop")),
            _lua_quote(style.get("preview_bg", "#18181D")),
        )
        for style in STYLES.values()
    )
    with open(script_entry, "r", encoding="utf-8") as source:
        script_content = source.read().replace(
            "__AUTO_CAPTION_PROJECT_DIR__",
            base_dir.replace("\\", "/"),
        )
    style_placeholder = "local styles = {}"
    if style_placeholder not in script_content:
        raise RuntimeError("AutoCaption.lua is missing the style catalog placeholder.")
    script_content = script_content.replace(
        style_placeholder,
        "local styles = {\n" + lua_styles + "\n}",
        1,
    )
    with open(target_script, "w", encoding="utf-8") as target:
        target.write(script_content)

    # Remove the previous Python menu entries so Resolve uses the native panel.
    for script_folder_to_clean in (paths["scripts_utility"], paths["scripts_edit"]):
        old_python_entry = os.path.join(script_folder_to_clean, "AutoCaption.py")
        if os.path.isfile(old_python_entry):
            os.remove(old_python_entry)
    installed_scripts = [target_script]

    return {
        "success": True,
        "templates_count": len(installed_templates),
        "target_titles_dir": target_titles_dir,
        "installed_scripts": installed_scripts
    }

def main():
    print("=" * 65)
    print(" [!] Auto Caption Plugin Installer - DaVinci Resolve Free v21")
    print("=" * 65)

    res = install_all()
    if res["success"]:
        print(f"\n[OK] Successfully installed {res['templates_count']} Drag-and-Drop Caption Styles!")
        print(f"    Destination: {res['target_titles_dir']}")
        print(f"\n[OK] Successfully installed Resolve Scripts to:")
        for s in res["installed_scripts"]:
            print(f"    -> {s}")

        print("\n" + "=" * 65)
        print(" HOW TO USE IN DAVINCI RESOLVE:")
        print(" 1. In DaVinci Resolve, go to Effects > Titles > Auto Captions")
        print(f"    You will see {res['templates_count']} drag-and-drop styles ready to use!")
        print(" 2. To Auto-Transcribe & Generate Captions:")
        print("    Go to Workspace > Scripts > Utility > AutoCaption")
        print("    OR double-click 'AutoCaption.command' on your Mac.")
        print("=" * 65)
    else:
        print("[!] Installation encountered an error.")

if __name__ == "__main__":
    main()
