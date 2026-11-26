#!/usr/bin/env python3
"""
Generates all DaVinci Resolve Fusion Title .setting files
and packages them into the AutoCaptions.drfx bundle.
"""

import os
import re
import zipfile

from core.styles import STYLES, get_animation_preset

TEMPLATES = {
    "Hormozi Viral": {
        "description": "Bold yellow viral text with thick black outline, drop shadow, and punchy pop scale animation.",
        "font": "Impact",
        "style": "Regular",
        "size": 0.08,
        "center_y": 0.22,
        "fill": (1.0, 0.90, 0.0, 1.0),
        "outline": {"thickness": 0.026, "color": (0.0, 0.0, 0.0, 1.0)},
        "shadow": {"offset": (0.007, -0.007), "softness": 2, "alpha": 0.95},
        "animated": True,
        "animation": "pop_bounce",
    },
    "TikTok Bounce": {
        "description": "High contrast white text with crisp black border and dynamic bounce entrance.",
        "font": "Arial Black",
        "style": "Regular",
        "size": 0.075,
        "center_y": 0.22,
        "fill": (1.0, 1.0, 1.0, 1.0),
        "outline": {"thickness": 0.022, "color": (0.0, 0.0, 0.0, 1.0)},
        "shadow": {"offset": (0.006, -0.006), "softness": 4, "alpha": 0.90},
        "animated": True,
        "animation": "pop_bounce",
    },
    "MrBeast Highlighter": {
        "description": "Vibrant lime neon highlight text with heavy comic outline and hard drop shadow.",
        "font": "Impact",
        "style": "Regular",
        "size": 0.082,
        "center_y": 0.24,
        "fill": (0.22, 1.0, 0.15, 1.0),
        "outline": {"thickness": 0.030, "color": (0.0, 0.0, 0.0, 1.0)},
        "shadow": {"offset": (0.008, -0.008), "softness": 0, "alpha": 1.0},
        "animated": True,
        "animation": "comic_slam",
    },
    "Cinematic Box": {
        "description": "Clean modern sans-serif typography inside an elegant semi-transparent rounded dark box.",
        "font": "Helvetica Neue",
        "style": "Medium",
        "size": 0.055,
        "center_y": 0.16,
        "fill": (0.98, 0.98, 0.98, 1.0),
        "box": {
            "color": (0.06, 0.06, 0.08, 0.72),
            "pad_h": 0.06,
            "pad_v": 0.035,
            "round": 0.06,
        },
        "shadow": {"offset": (0.003, -0.004), "softness": 6, "alpha": 0.60},
        "animated": True,
        "animation": "slide_up",
    },
    "Cyber Neon": {
        "description": "Futuristic electric cyan text with multi-layer glowing outline and magenta atmospheric back glow.",
        "font": "Arial Black",
        "style": "Regular",
        "size": 0.075,
        "center_y": 0.22,
        "fill": (0.0, 0.96, 1.0, 1.0),
        "outline": {"thickness": 0.014, "color": (0.0, 0.65, 1.0, 0.9), "softness": 12},
        "ambient_glow": {"thickness": 0.035, "color": (0.85, 0.0, 0.85, 0.55), "softness": 28},
        "animated": True,
        "animation": "neon_pulse",
    },
    "Clean Minimalist": {
        "description": "Distraction-free, crisp white subtitle with gentle diffused shadow for corporate & documentary.",
        "font": "Helvetica",
        "style": "Regular",
        "size": 0.052,
        "center_y": 0.14,
        "fill": (0.98, 0.98, 0.98, 1.0),
        "outline": {"thickness": 0.005, "color": (0.0, 0.0, 0.0, 0.50)},
        "shadow": {"offset": (0.0, -0.004), "softness": 8, "alpha": 0.75},
        "animated": True,
        "animation": "soft_rise",
    },
    "Retro Comic Pop": {
        "description": "Retro comic style with warm gold text, black border, and extruded red 3D drop shadow.",
        "font": "Impact",
        "style": "Regular",
        "size": 0.080,
        "center_y": 0.22,
        "fill": (1.0, 0.85, 0.0, 1.0),
        "outline": {"thickness": 0.024, "color": (0.0, 0.0, 0.0, 1.0)},
        "extrusion": {"offset": (0.012, -0.012), "color": (0.92, 0.15, 0.15, 1.0), "thickness": 0.024},
        "animated": True,
        "animation": "comic_slam",
    },
    "Split Tone": {
        "description": "Two-tone gradient caption with vibrant yellow top, white base, and bold contrast outline.",
        "font": "Arial Black",
        "style": "Regular",
        "size": 0.078,
        "center_y": 0.22,
        "gradient": True,
        "outline": {"thickness": 0.022, "color": (0.0, 0.0, 0.0, 1.0)},
        "shadow": {"offset": (0.006, -0.006), "softness": 2, "alpha": 0.90},
        "animated": True,
        "animation": "slide_pop",
    },
}

for style_name, style in STYLES.items():
    if style_name not in TEMPLATES and "template_config" in style:
        TEMPLATES[style_name] = style["template_config"]


def _format_bezier_spline(name: str, color: tuple[int, int, int], points: list[tuple[int, float]], smooth: bool = False) -> str:
    """Format a Fusion BezierSpline block for a list of (frame, value) keyframes."""
    r, g, b = color
    lines = []
    last_idx = len(points) - 1
    for idx, (frame, value) in enumerate(points):
        if smooth and len(points) >= 2:
            parts = [f"{value:.6g}"]
            if idx > 0:
                prev_f, _ = points[idx - 1]
                lh_x = -max(0.5, (frame - prev_f) * 0.45)
                parts.append(f"LH = {{ {lh_x:.4g}, 0 }}")
            if idx < last_idx:
                next_f, next_v = points[idx + 1]
                rh_x = max(0.5, (next_f - frame) * 0.35)
                rh_y = (next_v - value) * 0.75
                parts.append(f"RH = {{ {rh_x:.4g}, {rh_y:.6g} }}")
            entry = ", ".join(parts)
        else:
            entry = f"{value:.6g}, Flags = {{ Linear = true }}"
        comma = "," if idx < last_idx else ""
        lines.append(f"\t\t\t\t[{frame}] = {{ {entry} }}{comma}")
    keyframes_block = "\n".join(lines)
    return (
        f"\t\t{name} = BezierSpline {{\n"
        f"\t\t\tSplineColor = {{ Red = {r}, Green = {g}, Blue = {b} }},\n"
        f"\t\t\tKeyFrames = {{\n"
        f"{keyframes_block}\n"
        f"\t\t\t}}\n"
        f"\t\t}}"
    )


def _build_fusion_animation(config: dict, center_y: float):
    """Build Transform, FadeMerge, KeyStretcher inputs and root spline modifiers."""
    preset = get_animation_preset(config.get("animation", "pop_bounce"))
    smooth = bool(preset.get("smooth", False))
    base_frames = int(preset.get("base_frames", 10))
    stretch_start = base_frames + 1

    transform_inputs = [
        '\t\t\t\t\t\tInput = Input {\n\t\t\t\t\t\t\tSourceOp = "Template",\n\t\t\t\t\t\t\tSource = "Output",\n\t\t\t\t\t\t},',
        f'\t\t\t\t\t\tPivot = Input {{ Value = {{ 0.5, {center_y} }}, }},',
    ]
    modifiers = []

    offset_points = preset.get("offset")
    if offset_points:
        has_x = any(dx != 0.0 for _, dx, _ in offset_points)
        has_y = any(dy != 0.0 for _, _, dy in offset_points)
        if has_x or has_y:
            transform_inputs.append(
                '\t\t\t\t\t\tCenter = Input {\n\t\t\t\t\t\t\tSourceOp = "AnimCenterPath",\n\t\t\t\t\t\t\tSource = "Value",\n\t\t\t\t\t\t},'
            )
            xy_inputs = []
            if has_x:
                xy_inputs.append('\t\t\t\tX = Input {\n\t\t\t\t\tSourceOp = "AnimCenterX",\n\t\t\t\t\tSource = "Value",\n\t\t\t\t},')
                modifiers.append(
                    _format_bezier_spline(
                        "AnimCenterX",
                        (255, 80, 80),
                        [(f, 0.5 + dx) for f, dx, _ in offset_points],
                        smooth=smooth,
                    )
                )
            else:
                xy_inputs.append('\t\t\t\tX = Input { Value = 0.5, },')

            if has_y:
                xy_inputs.append('\t\t\t\tY = Input {\n\t\t\t\t\tSourceOp = "AnimCenterY",\n\t\t\t\t\tSource = "Value",\n\t\t\t\t},')
                modifiers.append(
                    _format_bezier_spline(
                        "AnimCenterY",
                        (80, 220, 120),
                        [(f, 0.5 + dy) for f, _, dy in offset_points],
                        smooth=smooth,
                    )
                )
            else:
                xy_inputs.append('\t\t\t\tY = Input { Value = 0.5, },')

            xy_inputs_str = "\n".join(xy_inputs)
            modifiers.append(
                "\t\tAnimCenterPath = XYPath {\n"
                "\t\t\tShowKeyPoints = false,\n"
                '\t\t\tDrawMode = "ModifyOnly",\n'
                "\t\t\tCtrlWZoom = false,\n"
                "\t\t\tInputs = {\n"
                f"{xy_inputs_str}\n"
                "\t\t\t}\n"
                "\t\t}"
            )

    scale_points = preset.get("scale")
    if scale_points:
        transform_inputs.append(
            '\t\t\t\t\t\tSize = Input {\n\t\t\t\t\t\t\tSourceOp = "AnimSizeSpline",\n\t\t\t\t\t\t\tSource = "Value",\n\t\t\t\t\t\t},'
        )
        modifiers.append(
            _format_bezier_spline("AnimSizeSpline", (255, 200, 0), scale_points, smooth=smooth)
        )

    rotation_points = preset.get("rotation")
    if rotation_points:
        transform_inputs.append(
            '\t\t\t\t\t\tAngle = Input {\n\t\t\t\t\t\t\tSourceOp = "AnimAngleSpline",\n\t\t\t\t\t\t\tSource = "Value",\n\t\t\t\t\t\t},'
        )
        modifiers.append(
            _format_bezier_spline("AnimAngleSpline", (120, 170, 255), rotation_points, smooth=smooth)
        )

    opacity_points = list(preset.get("opacity", [(0, 1.0)]))
    outro_opacity = preset.get("outro_opacity")
    if outro_opacity:
        opacity_points.extend(outro_opacity)
        stretch_end = 114
    else:
        stretch_end = 119
    modifiers.append(
        _format_bezier_spline("AnimOpacitySpline", (200, 120, 255), opacity_points, smooth=smooth)
    )

    return "\n".join(transform_inputs), ",\n".join(modifiers), stretch_start, stretch_end


def generate_setting_file(name, config):
    font = config["font"]
    style = config["style"]
    size = config["size"]
    center_y = config["center_y"]
    animated = config.get("animated", False)
    
    # Base inputs
    inputs_lua = [
        '				Width = Input { Value = 1920, },',
        '				Height = Input { Value = 1080, },',
        '				UseFrameFormatSettings = Input { Value = 1, },',
        '				["Gamut.SLogVersion"] = Input { Value = FuID { "SLog2" }, },',
        f'				Center = Input {{ Value = {{ 0.5, {center_y} }}, }},',
        '				StyledText = Input { Value = "SAMPLE CAPTION", },',
        f'				Font = Input {{ Value = "{font}", }},',
        f'				Style = Input {{ Value = "{style}", }},',
        f'				Size = Input {{ Value = {size}, }},',
        '				VerticalJustificationNew = Input { Value = 3, },',
        '				HorizontalJustificationNew = Input { Value = 3, },',
        '				TransformRotation = Input { Value = 1, },',
        '				TransformSize = Input { Value = 1, },',
    ]

    # Element 1: Fill
    gradient = config.get("gradient")
    if gradient:
        if isinstance(gradient, dict):
            gradient_colors = gradient["colors"]
        else:
            gradient_colors = ((1.0, 0.88, 0.0, 1.0), (1.0, 1.0, 1.0, 1.0))
        first_color, second_color = gradient_colors
        inputs_lua.extend([
            '				Name1 = Input { Value = "Gradient Fill", },',
            '				Type1 = Input { Value = 2, },',
            '				ShadingGradient1 = Input {',
            '					Value = Gradient {',
            '						Colors = {',
            f'							[0] = {{ {first_color[0]}, {first_color[1]}, {first_color[2]}, {first_color[3]} }},',
            f'							[1] = {{ {second_color[0]}, {second_color[1]}, {second_color[2]}, {second_color[3]} }}',
            '						}',
            '					},',
            '				},',
            '				ShadingMappingAngle1 = Input { Value = 90, },',
        ])
    else:
        r, g, b, a = config["fill"]
        inputs_lua.extend([
            '				Name1 = Input { Value = "Solid Fill", },',
            f'				Red1 = Input {{ Value = {r}, }},',
            f'				Green1 = Input {{ Value = {g}, }},',
            f'				Blue1 = Input {{ Value = {b}, }},',
            f'				Alpha1 = Input {{ Value = {a}, }},',
        ])

    # Element 2: Outline
    if "outline" in config:
        out = config["outline"]
        thick = out["thickness"]
        r, g, b, a = out["color"]
        soft = out.get("softness", 0)
        inputs_lua.extend([
            '				Name2 = Input { Value = "Stroke Outline", },',
            '				Enabled2 = Input { Value = 1, },',
            '				Type2 = Input { Value = 1, },',
            f'				Thickness2 = Input {{ Value = {thick}, }},',
            f'				Red2 = Input {{ Value = {r}, }},',
            f'				Green2 = Input {{ Value = {g}, }},',
            f'				Blue2 = Input {{ Value = {b}, }},',
            f'				Alpha2 = Input {{ Value = {a}, }},',
            '				PriorityBack2 = Input { Value = 9, },',
        ])
        if soft > 0:
            inputs_lua.extend([
                '				Softness2 = Input { Value = 1, },',
                f'				SoftnessX2 = Input {{ Value = {soft}, }},',
                f'				SoftnessY2 = Input {{ Value = {soft}, }},',
            ])

    # Element 3: Shadow
    if "shadow" in config:
        sh = config["shadow"]
        ox, oy = sh["offset"]
        shadow_color = sh.get("color", (0.0, 0.0, 0.0, 1.0))
        red, green, blue, _ = shadow_color
        soft = sh.get("softness", 0)
        alpha = sh.get("alpha", 0.85)
        inputs_lua.extend([
            '				Name3 = Input { Value = "Drop Shadow", },',
            '				Enabled3 = Input { Value = 1, },',
            '				Type3 = Input { Value = 1, },',
            f'				Red3 = Input {{ Value = {red}, }},',
            f'				Green3 = Input {{ Value = {green}, }},',
            f'				Blue3 = Input {{ Value = {blue}, }},',
            f'				Alpha3 = Input {{ Value = {alpha}, }},',
            f'				Offset3 = Input {{ Value = {{ {ox}, {oy} }}, }},',
        ])
        if soft > 0:
            inputs_lua.extend([
                '				Softness3 = Input { Value = 1, },',
                f'				SoftnessX3 = Input {{ Value = {soft}, }},',
                f'				SoftnessY3 = Input {{ Value = {soft}, }},',
            ])

    # Element 4: Box (for Cinematic Box)
    if "box" in config:
        bx = config["box"]
        r, g, b, a = bx["color"]
        pad_h = bx["pad_h"]
        pad_v = bx["pad_v"]
        roundness = bx["round"]
        inputs_lua.extend([
            '				Name4 = Input { Value = "Backdrop Box", },',
            '				Enabled4 = Input { Value = 1, },',
            '				ElementShape4 = Input { Value = 2, },',  # Border/Box
            '				Level4 = Input { Value = 3, },',         # Entire Text
            f'				ExtendHorizontal4 = Input {{ Value = {pad_h}, }},',
            f'				ExtendVertical4 = Input {{ Value = {pad_v}, }},',
            f'				Round4 = Input {{ Value = {roundness}, }},',
            f'				Red4 = Input {{ Value = {r}, }},',
            f'				Green4 = Input {{ Value = {g}, }},',
            f'				Blue4 = Input {{ Value = {b}, }},',
            f'				Alpha4 = Input {{ Value = {a}, }},',
            '				PriorityBack4 = Input { Value = -10, },',
        ])

    # Element 4: Extrusion (for Comic Pop)
    if "extrusion" in config:
        ex = config["extrusion"]
        ox, oy = ex["offset"]
        r, g, b, a = ex["color"]
        thick = ex["thickness"]
        inputs_lua.extend([
            '				Name4 = Input { Value = "3D Red Extrusion", },',
            '				Enabled4 = Input { Value = 1, },',
            '				Type4 = Input { Value = 1, },',
            f'				Thickness4 = Input {{ Value = {thick}, }},',
            f'				Red4 = Input {{ Value = {r}, }},',
            f'				Green4 = Input {{ Value = {g}, }},',
            f'				Blue4 = Input {{ Value = {b}, }},',
            f'				Alpha4 = Input {{ Value = {a}, }},',
            f'				Offset4 = Input {{ Value = {{ {ox}, {oy} }}, }},',
            '				PriorityBack4 = Input { Value = 5, },',
        ])

    # Element 5: Ambient Glow (for Cyber Neon)
    if "ambient_glow" in config:
        glow = config["ambient_glow"]
        r, g, b, a = glow["color"]
        thick = glow["thickness"]
        soft = glow["softness"]
        inputs_lua.extend([
            '				Name5 = Input { Value = "Magenta Atmosphere Glow", },',
            '				Enabled5 = Input { Value = 1, },',
            '				Type5 = Input { Value = 1, },',
            f'				Thickness5 = Input {{ Value = {thick}, }},',
            f'				Red5 = Input {{ Value = {r}, }},',
            f'				Green5 = Input {{ Value = {g}, }},',
            f'				Blue5 = Input {{ Value = {b}, }},',
            f'				Alpha5 = Input {{ Value = {a}, }},',
            '				Softness5 = Input { Value = 1, },',
            f'				SoftnessX5 = Input {{ Value = {soft}, }},',
            f'				SoftnessY5 = Input {{ Value = {soft}, }},',
            '				PriorityBack5 = Input { Value = -5, },',
        ])

    inputs_str = "\n".join(inputs_lua)

    # If animated, wrap in a GroupOperator with Transform, FadeMerge, and KeyStretcher
    if animated:
        safe_tool_id = re.sub(r"[^A-Za-z0-9_]", "", name)
        transform_inputs, modifiers_str, stretch_start, stretch_end = _build_fusion_animation(config, center_y)
        content = f"""{{
	Tools = ordered() {{
		{safe_tool_id} = GroupOperator {{
			CtrlWZoom = false,
			Inputs = ordered() {{
				Input1 = InstanceInput {{
					SourceOp = "Template",
					Source = "StyledText",
					Page = "Controls",
				}},
				Input2 = InstanceInput {{
					SourceOp = "Template",
					Source = "Font",
					ControlGroup = 2,
					Page = "Controls",
				}},
				Input3 = InstanceInput {{
					SourceOp = "Template",
					Source = "Style",
					ControlGroup = 2,
					Page = "Controls",
				}},
				Input4 = InstanceInput {{
					SourceOp = "Template",
					Source = "Size",
					Default = {size},
					Page = "Controls",
				}},
				Input5 = InstanceInput {{
					SourceOp = "Template",
					Source = "Center",
					Page = "Controls",
				}},
				Input6 = InstanceInput {{
					SourceOp = "Template",
					Source = "CharacterSpacingClone",
					Name = "Tracking",
					Default = 1,
					Page = "Controls",
				}},
				Input7 = InstanceInput {{
					SourceOp = "Template",
					Source = "LineSpacingClone",
					Default = 1,
					Page = "Controls",
				}}
			}},
			Outputs = {{
				MainOutput1 = InstanceOutput {{
					SourceOp = "KeyframeStretcher1",
					Source = "Result",
					Name = "Output",
				}}
			}},
			Tools = ordered() {{
				Template = TextPlus {{
					CtrlWZoom = false,
					NameSet = true,
					Inputs = {{
{inputs_str}
					}},
					ViewInfo = OperatorInfo {{ Pos = {{ 10, 10 }} }},
				}},
				AnimTransform = Transform {{
					CtrlWZoom = false,
					Inputs = {{
{transform_inputs}
					}},
					ViewInfo = OperatorInfo {{ Pos = {{ 120, 10 }} }},
				}},
				TransparentBG = Background {{
					CtrlWZoom = false,
					Inputs = {{
						Width = Input {{ Value = 1920, }},
						Height = Input {{ Value = 1080, }},
						UseFrameFormatSettings = Input {{ Value = 1, }},
						["Gamut.SLogVersion"] = Input {{ Value = FuID {{ "SLog2" }}, }},
						TopLeftAlpha = Input {{ Value = 0, }},
					}},
					ViewInfo = OperatorInfo {{ Pos = {{ 120, 90 }} }},
				}},
				FadeMerge = Merge {{
					CtrlWZoom = false,
					Inputs = {{
						Background = Input {{
							SourceOp = "TransparentBG",
							Source = "Output",
						}},
						Foreground = Input {{
							SourceOp = "AnimTransform",
							Source = "Output",
						}},
						Blend = Input {{
							SourceOp = "AnimOpacitySpline",
							Source = "Value",
						}},
						PerformDepthMerge = Input {{ Value = 0, }},
					}},
					ViewInfo = OperatorInfo {{ Pos = {{ 230, 10 }} }},
				}},
				KeyframeStretcher1 = KeyStretcher {{
					Inputs = {{
						Keyframes = Input {{
							SourceOp = "FadeMerge",
							Source = "Output",
						}},
						SourceEnd = Input {{ Value = 120, }},
						StretchStart = Input {{ Value = {stretch_start}, }},
						StretchEnd = Input {{ Value = {stretch_end}, }},
					}},
					ViewInfo = OperatorInfo {{ Pos = {{ 340, 10 }} }},
				}}
			}},
		}},
{modifiers_str}
	}},
	ActiveTool = "{safe_tool_id}"
}}
"""
    else:
        content = f"""{{
	Tools = ordered() {{
		Template = TextPlus {{
			CtrlWZoom = false,
			NameSet = true,
			Inputs = {{
{inputs_str}
			}},
			ViewInfo = OperatorInfo {{ Pos = {{ 720, 84.3333 }} }},
		}}
	}},
	ActiveTool = "Template"
}}
"""
    return content

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    templates_dir = os.path.join(base_dir, "templates")
    dist_dir = os.path.join(base_dir, "dist")
    os.makedirs(templates_dir, exist_ok=True)
    os.makedirs(dist_dir, exist_ok=True)

    drfx_path = os.path.join(dist_dir, "AutoCaptions.drfx")
    with zipfile.ZipFile(drfx_path, "w", zipfile.ZIP_DEFLATED) as drfx:
        for name, config in TEMPLATES.items():
            content = generate_setting_file(name, config)
            file_name = f"{name}.setting"
            setting_path = os.path.join(templates_dir, file_name)
            with open(setting_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"Generated template: {file_name}")

            # Add to .drfx under Edit/Titles/Auto Captions/
            arc_name = f"Edit/Titles/Auto Captions/{file_name}"
            drfx.writestr(arc_name, content)
            print(f"  -> Added to DRFX: {arc_name}")

    print(f"\nCreated DRFX bundle: {drfx_path} ({os.path.getsize(drfx_path)} bytes)")

if __name__ == "__main__":
    main()
