"""
Caption style presets and metadata for DaVinci Resolve.
"""

STYLES = {
    "Hormozi Viral": {
        "id": "HormoziViral",
        "name": "Hormozi Viral",
        "preview_kind": "pop",
        "description": "Bold yellow viral text with thick black outline & pop bounce",
        "font": "Impact",
        "style": "Regular",
        "color_hex": "#FFE600",
        "color_rgb": (1.0, 0.90, 0.0),
        "stroke_hex": "#000000",
        "stroke_width": 4,
        "animated": True,
        "default_chunk": "short",  # 2-3 words
        "default_case": "UPPERCASE",
        "template_file": "Hormozi Viral.setting",
    },
    "TikTok Bounce": {
        "id": "TikTokBounce",
        "name": "TikTok Bounce",
        "preview_kind": "pop",
        "description": "High contrast white text with crisp black border & bounce entrance",
        "font": "Arial Black",
        "style": "Regular",
        "color_hex": "#FFFFFF",
        "color_rgb": (1.0, 1.0, 1.0),
        "stroke_hex": "#000000",
        "stroke_width": 3,
        "animated": True,
        "default_chunk": "short",
        "default_case": "UPPERCASE",
        "template_file": "TikTok Bounce.setting",
    },
    "MrBeast Highlighter": {
        "id": "MrBeastHighlighter",
        "name": "MrBeast Highlighter",
        "preview_kind": "comic",
        "description": "Vibrant lime neon highlight text with comic drop shadow",
        "font": "Impact",
        "style": "Regular",
        "color_hex": "#39FF14",
        "color_rgb": (0.22, 1.0, 0.15),
        "stroke_hex": "#000000",
        "stroke_width": 4,
        "animated": True,
        "default_chunk": "short",
        "default_case": "UPPERCASE",
        "template_file": "MrBeast Highlighter.setting",
    },
    "Cinematic Box": {
        "id": "CinematicBox",
        "name": "Cinematic Box",
        "preview_kind": "box",
        "preview_bg": "#101014",
        "description": "Clean modern typography inside a rounded dark translucent box",
        "font": "Helvetica Neue",
        "style": "Medium",
        "color_hex": "#FAFAFA",
        "color_rgb": (0.98, 0.98, 0.98),
        "stroke_hex": None,
        "stroke_width": 0,
        "animated": False,
        "box_hex": "#101014",
        "box_opacity": 0.72,
        "default_chunk": "balanced",  # 4-6 words
        "default_case": "Original",
        "template_file": "Cinematic Box.setting",
    },
    "Cyber Neon": {
        "id": "CyberNeon",
        "name": "Cyber Neon",
        "preview_kind": "neon",
        "description": "Futuristic electric cyan with multi-layer glowing outline & ambiance",
        "font": "Arial Black",
        "style": "Regular",
        "color_hex": "#00F5FF",
        "color_rgb": (0.0, 0.96, 1.0),
        "stroke_hex": "#0066FF",
        "stroke_width": 2,
        "animated": True,
        "default_chunk": "short",
        "default_case": "UPPERCASE",
        "template_file": "Cyber Neon.setting",
    },
    "Clean Minimalist": {
        "id": "CleanMinimalist",
        "name": "Clean Minimalist",
        "preview_kind": "clean",
        "description": "Clean white subtitle with soft shadow for podcasts and documentaries",
        "font": "Helvetica",
        "style": "Regular",
        "color_hex": "#FFFFFF",
        "color_rgb": (1.0, 1.0, 1.0),
        "stroke_hex": "#000000",
        "stroke_width": 1,
        "animated": False,
        "default_chunk": "balanced",
        "default_case": "Original",
        "template_file": "Clean Minimalist.setting",
    },
    "Retro Comic Pop": {
        "id": "RetroComicPop",
        "name": "Retro Comic Pop",
        "preview_kind": "comic",
        "description": "Cartoon comic pop with gold text and extruded red 3D shadow",
        "font": "Impact",
        "style": "Regular",
        "color_hex": "#FFD700",
        "color_rgb": (1.0, 0.84, 0.0),
        "stroke_hex": "#000000",
        "stroke_width": 4,
        "animated": True,
        "default_chunk": "1_word",
        "default_case": "UPPERCASE",
        "template_file": "Retro Comic Pop.setting",
    },
    "Split Tone": {
        "id": "SplitTone",
        "name": "Split Tone",
        "preview_kind": "gradient",
        "description": "Gold gradient top with crisp white base and dark outline",
        "font": "Arial Black",
        "style": "Regular",
        "color_hex": "#FFE600",
        "color_rgb": (1.0, 0.90, 0.0),
        "stroke_hex": "#000000",
        "stroke_width": 3,
        "animated": True,
        "default_chunk": "short",
        "default_case": "UPPERCASE",
        "template_file": "Split Tone.setting",
    },
}


_PALETTES = (
    ("Lemon", "#FFE600", "#FF9F1C", "#241B00"),
    ("Cyan", "#00E5FF", "#287BFF", "#001923"),
    ("Pink", "#FF4FA3", "#B82EFF", "#250916"),
    ("Lime", "#9DFF00", "#00C78B", "#101D00"),
    ("Orange", "#FF7628", "#FF2948", "#241006"),
    ("Violet", "#B46CFF", "#00D1FF", "#180B25"),
    ("Ice Blue", "#86E6FF", "#3B82F6", "#071823"),
    ("Rose Gold", "#FFB07C", "#FF4D6D", "#24120D"),
)

_FAMILIES = (
    ("Viral Pop", "pop", "Impact", "Bold color with a heavy outline and punchy pop entrance."),
    ("Neon Glow", "neon", "Arial Black", "Electric color with a soft neon halo."),
    ("Comic Burst", "comic", "Impact", "Comic-book color, thick ink outline, and offset extrusion."),
    ("Glass Caption", "box", "Helvetica Neue", "Clean white type on a tinted translucent caption panel."),
    ("Clean Creator", "clean", "Helvetica", "Minimal white captions with a soft, restrained shadow."),
    ("Outline Flash", "outline", "Arial Black", "White type with a vivid colored outline."),
    ("Gradient Rush", "gradient", "Arial Black", "Two-tone gradient with a bold outline and pop entrance."),
    ("Shadow Pop", "shadow", "Impact", "Bright type with a hard colored shadow and pop entrance."),
)


def _hex_rgba(value: str, alpha: float = 1.0) -> tuple[float, float, float, float]:
    value = value.lstrip("#")
    return (
        int(value[0:2], 16) / 255,
        int(value[2:4], 16) / 255,
        int(value[4:6], 16) / 255,
        alpha,
    )


def _make_variant(name: str, family: str, kind: str, font: str, description: str,
                  palette_name: str, fill_hex: str, accent_hex: str,
                  dark_hex: str) -> dict:
    is_light = kind in {"box", "clean", "outline"}
    text_hex = "#FFFFFF" if is_light else fill_hex
    stroke_hex = accent_hex if kind == "outline" else dark_hex if kind == "clean" else "#000000"
    stroke_width = 1 if kind == "clean" else 5 if kind == "outline" else 4 if kind in {"pop", "comic"} else 3
    fill = _hex_rgba(text_hex)
    dark = _hex_rgba(dark_hex)
    accent = _hex_rgba(accent_hex)
    black = _hex_rgba("#000000")

    template = {
        "description": description,
        "font": font,
        "style": "Regular",
        "size": 0.078 if kind in {"pop", "comic", "outline", "gradient", "shadow"} else 0.058,
        "center_y": 0.22 if kind not in {"box", "clean"} else 0.16,
        "fill": fill,
        "animated": True,
    }

    if kind == "neon":
        template["outline"] = {
            "thickness": 0.014,
            "color": accent,
            "softness": 8,
        }
        template["ambient_glow"] = {
            "thickness": 0.035,
            "color": _hex_rgba(accent_hex, 0.55),
            "softness": 24,
        }
    elif kind == "comic":
        template["outline"] = {"thickness": 0.03, "color": black}
        template["extrusion"] = {
            "offset": (0.012, -0.012),
            "color": accent,
            "thickness": 0.024,
        }
    elif kind == "box":
        template["box"] = {
            "color": _hex_rgba(dark_hex, 0.82),
            "pad_h": 0.06,
            "pad_v": 0.035,
            "round": 0.06,
        }
        template["shadow"] = {
            "offset": (0.003, -0.004),
            "softness": 6,
            "alpha": 0.6,
        }
    elif kind == "clean":
        template["outline"] = {
            "thickness": 0.005,
            "color": _hex_rgba(dark_hex, 0.5),
        }
        template["shadow"] = {
            "offset": (0.0, -0.004),
            "softness": 8,
            "alpha": 0.75,
        }
    elif kind == "outline":
        template["outline"] = {"thickness": 0.03, "color": accent}
        template["shadow"] = {
            "offset": (0.006, -0.006),
            "softness": 2,
            "alpha": 0.85,
        }
    elif kind == "gradient":
        template["gradient"] = {
            "colors": (fill, _hex_rgba("#FFFFFF")),
        }
        template["outline"] = {"thickness": 0.022, "color": black}
        template["shadow"] = {
            "offset": (0.006, -0.006),
            "softness": 2,
            "alpha": 0.9,
        }
    elif kind == "shadow":
        template["outline"] = {"thickness": 0.012, "color": dark}
        template["shadow"] = {
            "offset": (0.01, -0.01),
            "softness": 0,
            "alpha": 0.95,
            "color": accent,
        }
    else:
        template["outline"] = {"thickness": 0.026, "color": black}
        template["shadow"] = {
            "offset": (0.007, -0.007),
            "softness": 2,
            "alpha": 0.95,
        }

    return {
        "id": "".join(character for character in name if character.isalnum()),
        "name": name,
        "family": family,
        "preview_kind": kind,
        "preview_bg": dark_hex if kind == "box" else "#18181D",
        "description": f"{description} {palette_name} palette.",
        "font": font,
        "style": "Regular",
        "color_hex": text_hex,
        "color_rgb": fill[:3],
        "preview_accent": accent_hex,
        "stroke_hex": stroke_hex,
        "stroke_rgb": _hex_rgba(stroke_hex)[:3],
        "stroke_width": stroke_width,
        "animated": True,
        "default_chunk": "short",
        "default_case": "UPPERCASE",
        "template_file": f"{name}.setting",
        "template_config": template,
    }


for family, kind, font, description in _FAMILIES:
    for palette_name, fill_hex, accent_hex, dark_hex in _PALETTES:
        style_name = f"{family} - {palette_name}"
        STYLES[style_name] = _make_variant(
            style_name,
            family,
            kind,
            font,
            description,
            palette_name,
            fill_hex,
            accent_hex,
            dark_hex,
        )


def get_style(name):
    return STYLES.get(name, STYLES["Hormozi Viral"])
