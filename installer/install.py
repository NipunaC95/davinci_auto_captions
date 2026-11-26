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

def install_all():
    """Installs template styles and scripts into DaVinci Resolve directories."""
    paths = get_resolve_support_paths()
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    templates_src = os.path.join(base_dir, "templates")
    drfx_src = os.path.join(base_dir, "dist", "AutoCaptions.drfx")
    core_src = os.path.join(base_dir, "core")
    ui_src = os.path.join(base_dir, "ui")

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

    # 3. Install Resolve Scripts
    script_entry = os.path.join(base_dir, "AutoCaption.py")
    installed_scripts = []
    for script_folder in [paths["scripts_utility"], paths["scripts_edit"]]:
        os.makedirs(script_folder, exist_ok=True)
        target_script = os.path.join(script_folder, "AutoCaption.py")
        shutil.copy2(script_entry, target_script)
        with open(os.path.join(script_folder, "AutoCaption.project"), "w", encoding="utf-8") as marker:
            marker.write(base_dir)
        installed_scripts.append(target_script)

        # Copy runtime modules next to the installed entry script so it works
        # independently of the original repository checkout.
        for src_dir, dirname in ((core_src, "core"), (ui_src, "ui")):
            dst_dir = os.path.join(script_folder, dirname)
            if os.path.isdir(dst_dir):
                shutil.rmtree(dst_dir)
            shutil.copytree(src_dir, dst_dir)

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
        print(f"\n[✓] Successfully installed {res['templates_count']} Drag-and-Drop Caption Styles!")
        print(f"    Destination: {res['target_titles_dir']}")
        print(f"\n[✓] Successfully installed Resolve Scripts to:")
        for s in res["installed_scripts"]:
            print(f"    -> {s}")

        print("\n" + "=" * 65)
        print(" HOW TO USE IN DAVINCI RESOLVE:")
        print(" 1. In DaVinci Resolve, go to Effects > Titles > Auto Captions")
        print("    You will see all 8 drag-and-drop styles ready to use!")
        print(" 2. To Auto-Transcribe & Generate Captions:")
        print("    Go to Workspace > Scripts > Utility > AutoCaption")
        print("    OR double-click 'AutoCaption.command' on your Mac.")
        print("=" * 65)
    else:
        print("[!] Installation encountered an error.")

if __name__ == "__main__":
    main()
