"""
FCPXML and FCP 7 XML generator for importing styled caption clips
directly into DaVinci Resolve Free v21 timelines.
"""

import os
from typing import List, Optional
from core.transcriber import CaptionSegment
from core.styles import get_style

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
            f'            </title>'
        ])
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
