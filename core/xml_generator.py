"""
FCPXML and FCP 7 XML generator for importing styled caption clips
directly into DaVinci Resolve Free v21 timelines.
"""

import os
from typing import List, Optional
from core.transcriber import CaptionSegment
from core.styles import get_style, get_animation_preset


def _scale_keyframes(points, duration_frames: int, base_frames: int):
    """Map preset keyframes onto [0, duration_frames - 1] with strictly increasing times."""
    if not points or duration_frames <= 1:
        return []
    max_frame = duration_frames - 1
    if max_frame >= base_frames:
        return [(frame, value) for frame, value in points]

    mapped = []
    last_frame = -1
    for idx, (frame, value) in enumerate(points):
        if idx == len(points) - 1:
            scaled = max_frame
        else:
            scaled = int(round(frame * max_frame / max(1, base_frames)))
            scaled = min(scaled, max_frame - 1)
        if scaled <= last_frame:
            if idx == len(points) - 1 and mapped:
                mapped[-1] = (max_frame, value)
            continue
        mapped.append((scaled, value))
        last_frame = scaled
    return mapped


def _build_keyframe_xml(param_name: str, keyframes, fps: float, format_value, curve: str = "", interp: str = "") -> list[str]:
    if not keyframes:
        return []
    lines = [
        f'                <param name="{param_name}">',
        '                  <keyframeAnimation>',
    ]
    for idx, (frame, val) in enumerate(keyframes):
        time_str = "0s" if frame == 0 else frames_to_fcpxml_time(frame, fps)
        val_str = format_value(val)
        attrs = [f'time="{time_str}"', f'value="{val_str}"']
        if interp and idx > 0:
            attrs.append(f'interp="{interp}"')
        if curve:
            attrs.append(f'curve="{curve if idx > 0 else "linear"}"')
        lines.append(f'                    <keyframe {" ".join(attrs)}/>')
    lines.extend([
        '                  </keyframeAnimation>',
        '                </param>',
    ])
    return lines

def seconds_to_frames(seconds: float, fps: float) -> int:
    return int(round(seconds * fps))

def frames_to_fcpxml_time(frames: int, fps: float) -> str:
    # FCPXML rational time format, e.g. "120/30s" or "1001/30000s"
    if fps == 29.97:
        return f"{frames * 1001}/30000s"
    elif fps == 23.976:
        return f"{frames * 1001}/24000s"
    elif fps == 59.94:
        return f"{frames * 1001}/60000s"
    else:
        int_fps = int(round(fps))
        return f"{frames}/{int_fps}s"

def generate_fcpxml(
    segments: List[CaptionSegment],
    output_path: str,
    fps: float = 30.0,
    width: int = 1920,
    height: int = 1080,
    style_name: str = "Hormozi Viral",
    timeline_name: str = "Auto Captions"
) -> str:
    """Generates an FCPXML 1.9 file importable directly into DaVinci Resolve."""
    style = get_style(style_name)
    font = style["font"]
    color_rgb = style.get("color_rgb", (1.0, 1.0, 1.0))
    stroke_width = style.get("stroke_width", 3)
    stroke_rgb = style.get("stroke_rgb", (0.0, 0.0, 0.0))
    stroke_color_str = f"{stroke_rgb[0]} {stroke_rgb[1]} {stroke_rgb[2]} 1"
    animated = style.get("animated", False)
    preset = get_animation_preset(style.get("animation", "pop_bounce"))

    color_str = f"{color_rgb[0]} {color_rgb[1]} {color_rgb[2]} 1"
    frame_dur = frames_to_fcpxml_time(1, fps)
    
    total_frames = 0
    if segments:
        total_frames = seconds_to_frames(segments[-1].end_time + 1.0, fps)
    total_duration_str = frames_to_fcpxml_time(max(total_frames, 30), fps)

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<!DOCTYPE fcpxml>',
        '<fcpxml version="1.9">',
        '  <resources>',
        f'    <format id="r1" name="FFVideoFormat{height}p{int(fps)}" frameDuration="{frame_dur}" width="{width}" height="{height}"/>',
        '    <effect id="r2" name="Basic Title" uid=".../Titles.localized/Bumper:Opener.localized/Basic Title.localized/Basic Title.moti"/>',
        '  </resources>',
        '  <library>',
        f'    <event name="{timeline_name}">',
        f'      <project name="{timeline_name}">',
        f'        <sequence format="r1" duration="{total_duration_str}" tcStart="0s" tcFormat="NDF">',
        '          <spine>',
    ]

    last_end_frame = 0

    for i, seg in enumerate(segments):
        start_frame = seconds_to_frames(seg.start_time, fps)
        end_frame = seconds_to_frames(seg.end_time, fps)
        duration_frames = max(1, end_frame - start_frame)

        # Gap between previous clip and this clip
        if start_frame > last_end_frame:
            gap_dur = frames_to_fcpxml_time(start_frame - last_end_frame, fps)
            gap_offset = frames_to_fcpxml_time(last_end_frame, fps)
            lines.append(f'            <gap name="Gap" offset="{gap_offset}" duration="{gap_dur}" start="0s"/>')

        clip_offset = frames_to_fcpxml_time(start_frame, fps)
        clip_duration = frames_to_fcpxml_time(duration_frames, fps)
        text_escaped = seg.text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
        ts_id = f"ts{i+1}"

        lines.extend([
            f'            <title ref="r2" offset="{clip_offset}" name="{text_escaped}" duration="{clip_duration}" start="0s">',
            f'              <text>',
            f'                <text-style ref="{ts_id}">{text_escaped}</text-style>',
            f'              </text>',
            f'              <text-style-def id="{ts_id}">',
            f'                <text-style font="{font}" fontSize="72" fontColor="{color_str}" bold="1" strokeColor="{stroke_color_str}" strokeWidth="{stroke_width}" alignment="center"/>',
            f'              </text-style-def>',
        ])
        if animated and duration_frames > 1:
            base_frames = int(preset.get("base_frames", 10))
            curve = "smooth" if preset.get("smooth") else "linear"

            transform_params = []
            offset_points = preset.get("offset")
            if offset_points:
                pos_kfs = _scale_keyframes(
                    [(f, (dx * 100.0, dy * 100.0)) for f, dx, dy in offset_points],
                    duration_frames,
                    base_frames,
                )
                transform_params.extend(
                    _build_keyframe_xml(
                        "position",
                        pos_kfs,
                        fps,
                        lambda v: f"{v[0]:g} {v[1]:g}",
                    )
                )

            scale_points = preset.get("scale")
            if scale_points:
                scale_kfs = _scale_keyframes(scale_points, duration_frames, base_frames)
                transform_params.extend(
                    _build_keyframe_xml(
                        "scale",
                        scale_kfs,
                        fps,
                        lambda v: f"{v:g} {v:g}",
                        curve=curve,
                    )
                )

            rotation_points = preset.get("rotation")
            if rotation_points:
                rot_kfs = _scale_keyframes(rotation_points, duration_frames, base_frames)
                transform_params.extend(
                    _build_keyframe_xml(
                        "rotation",
                        rot_kfs,
                        fps,
                        lambda v: f"{v:g}",
                        curve=curve,
                    )
                )

            if transform_params:
                lines.append('              <adjust-transform>')
                lines.extend(transform_params)
                lines.append('              </adjust-transform>')

            opacity_points = preset.get("opacity")
            if opacity_points:
                opacity_kfs = _scale_keyframes(opacity_points, duration_frames, base_frames)
                outro_opacity = preset.get("outro_opacity")
                if outro_opacity and duration_frames >= base_frames + 8:
                    fade_start = duration_frames - 5
                    fade_end = duration_frames - 1
                    if not opacity_kfs or opacity_kfs[-1][0] < fade_start:
                        opacity_kfs.extend([(fade_start, 1.0), (fade_end, outro_opacity[-1][1])])
                blend_params = _build_keyframe_xml(
                    "opacity",
                    opacity_kfs,
                    fps,
                    lambda v: f"{v:g}",
                    curve=curve,
                )
                if blend_params:
                    lines.append('              <adjust-blend>')
                    lines.extend(blend_params)
                    lines.append('              </adjust-blend>')
        lines.append('            </title>')
        last_end_frame = start_frame + duration_frames

    lines.extend([
        '          </spine>',
        '        </sequence>',
        '      </project>',
        '    </event>',
        '  </library>',
        '</fcpxml>'
    ])

    content = "\n".join(lines)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
    return output_path

def generate_fcp7_xml(
    segments: List[CaptionSegment],
    output_path: str,
    fps: float = 30.0,
    width: int = 1920,
    height: int = 1080,
    style_name: str = "Hormozi Viral",
    timeline_name: str = "Auto Captions"
) -> str:
    """Generates a standard Final Cut Pro 7 XML (<xmeml version='5'>) file."""
    style = get_style(style_name)
    font = style["font"]
    color_rgb = style.get("color_rgb", (1.0, 1.0, 1.0))
    timebase = int(round(fps))

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<!DOCTYPE xmeml>',
        '<xmeml version="5">',
        '  <sequence>',
        f'    <name>{timeline_name}</name>',
        f'    <duration>{seconds_to_frames(segments[-1].end_time + 1.0 if segments else 10, fps)}</duration>',
        '    <rate>',
        f'      <timebase>{timebase}</timebase>',
        '      <ntsc>FALSE</ntsc>',
        '    </rate>',
        '    <media>',
        '      <video>',
        '        <format>',
        '          <samplecharacteristics>',
        f'            <width>{width}</width>',
        f'            <height>{height}</height>',
        f'            <rate><timebase>{timebase}</timebase></rate>',
        '          </samplecharacteristics>',
        '        </format>',
        '        <track>',
    ]

    for i, seg in enumerate(segments):
        start_frame = seconds_to_frames(seg.start_time, fps)
        end_frame = seconds_to_frames(seg.end_time, fps)
        text_escaped = seg.text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
        
        red_255 = int(color_rgb[0] * 255)
        green_255 = int(color_rgb[1] * 255)
        blue_255 = int(color_rgb[2] * 255)

        lines.extend([
            f'          <generatoritem id="caption_{i+1}">',
            f'            <name>{text_escaped}</name>',
            f'            <duration>{end_frame - start_frame}</duration>',
            '            <rate>',
            f'              <timebase>{timebase}</timebase>',
            '            </rate>',
            f'            <start>{start_frame}</start>',
            f'            <end>{end_frame}</end>',
            '            <effect>',
            '              <name>Text</name>',
            '              <effectid>Text</effectid>',
            '              <effecttype>generator</effecttype>',
            '              <parameter>',
            '                <parameterid>str</parameterid>',
            '                <name>Text</name>',
            f'                <value>{text_escaped}</value>',
            '              </parameter>',
            '              <parameter>',
            '                <parameterid>font</parameterid>',
            '                <name>Font</name>',
            f'                <value>{font}</value>',
            '              </parameter>',
            '              <parameter>',
            '                <parameterid>textcolor</parameterid>',
            '                <name>Color</name>',
            '                <value>',
            '                  <alpha>255</alpha>',
            f'                  <red>{red_255}</red>',
            f'                  <green>{green_255}</green>',
            f'                  <blue>{blue_255}</blue>',
            '                </value>',
            '              </parameter>',
            '            </effect>',
            '          </generatoritem>',
        ])

    lines.extend([
        '        </track>',
        '      </video>',
        '    </media>',
        '  </sequence>',
        '</xmeml>'
    ])

    content = "\n".join(lines)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
    return output_path
