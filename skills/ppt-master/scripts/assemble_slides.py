#!/usr/bin/env python3
"""
Assemble Slides — Ráp content + images → SVG → PPTX

Input: slides_enriched.json + image_mapping.json + style_config.json
Output: svg_output/slide_XX.svg → exports/presentation.pptx

Usage:
    python3 assemble_slides.py <project_path>
"""

import sys
import os
import json
import subprocess
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))


# Canvas dimensions (16:9)
CANVAS_W = 1920
CANVAS_H = 1080


def assemble(project_path: Path) -> dict:
    """Assemble all slides into SVG files.

    Args:
        project_path: Project directory with enriched content and images.

    Returns:
        Dict with assembly results.
    """
    # Load data
    enriched_path = project_path / "slides_enriched.json"
    if not enriched_path.exists():
        raise FileNotFoundError(f"slides_enriched.json not found")

    slides = json.loads(enriched_path.read_text(encoding="utf-8"))

    # Load style config
    style = _load_style(project_path)

    # Load image mapping
    image_mapping = {}
    mapping_path = project_path / "image_mapping.json"
    if mapping_path.exists():
        image_mapping = json.loads(mapping_path.read_text(encoding="utf-8"))

    # Create output directory
    svg_dir = project_path / "svg_output"
    svg_dir.mkdir(parents=True, exist_ok=True)

    print(f"[assemble] Generating {len(slides)} SVG slides...")

    for slide in slides:
        num = slide.get("slide_number", 0)
        slide_type = slide.get("type", slide.get("layout_hint", "content"))
        title = slide.get("title", f"Slide {num}")
        content = slide.get("content", slide.get("content_raw", ""))
        bullet_points = slide.get("bullet_points", [])

        # Get image for this slide
        slide_key = f"slide_{num:02d}"
        images = image_mapping.get(slide_key, [])
        bg_image = images[0] if images else None

        # Resolve image path
        img_path = None
        if bg_image:
            candidate = project_path / "slides" / slide_key / "images" / bg_image
            if candidate.exists():
                img_path = str(candidate)

        # Generate SVG based on slide type
        if num == 1 or slide_type in ("title_slide", "title"):
            svg = _generate_title_slide(title, content, style, img_path)
        elif slide_type in ("closing", "end"):
            svg = _generate_closing_slide(title, content, style)
        else:
            svg = _generate_content_slide(title, content, bullet_points, style, img_path, num)

        # Write SVG
        svg_path = svg_dir / f"slide_{num:02d}.svg"
        svg_path.write_text(svg, encoding="utf-8")
        print(f"[assemble]   Slide {num}: {svg_path.name}")

    # Run post-processing
    print("[assemble] Running post-processing...")
    scripts_dir = Path(__file__).resolve().parent

    # Step 1: Create total.md for notes
    notes_dir = project_path / "notes"
    notes_dir.mkdir(exist_ok=True)
    total_notes = []
    for slide in slides:
        num = slide.get("slide_number", 0)
        content = slide.get("content", slide.get("content_raw", ""))
        note = f"## Slide {num}\n\n{content}\n"
        total_notes.append(note)
        (notes_dir / f"slide_{num:02d}.md").write_text(note, encoding="utf-8")
    (notes_dir / "total.md").write_text("\n".join(total_notes), encoding="utf-8")

    # Step 2: finalize_svg.py
    finalize_script = scripts_dir / "finalize_svg.py"
    if finalize_script.exists():
        print("[assemble] Running finalize_svg.py...")
        subprocess.run([sys.executable, str(finalize_script), str(project_path)],
                      capture_output=True, text=True, cwd=str(scripts_dir.parent.parent))

    # Step 3: svg_to_pptx.py
    pptx_script = scripts_dir / "svg_to_pptx.py"
    if pptx_script.exists():
        print("[assemble] Running svg_to_pptx.py...")
        result = subprocess.run([sys.executable, str(pptx_script), str(project_path)],
                              capture_output=True, text=True, cwd=str(scripts_dir.parent.parent))
        if result.returncode == 0:
            print("[assemble] PPTX exported successfully!")
        else:
            print(f"[assemble] PPTX export warning: {result.stderr[:300]}")

    return {
        "total_slides": len(slides),
        "svg_dir": str(svg_dir),
        "project_path": str(project_path),
    }


def _load_style(project_path: Path) -> dict:
    """Load style config or use defaults."""
    style_path = project_path / "style_config.json"
    if style_path.exists():
        return json.loads(style_path.read_text(encoding="utf-8"))

    return {
        "title": "Presentation",
        "colors": {
            "primary": "#1a1a2e",
            "secondary": "#16213e",
            "accent": "#4a90d9",
            "text": "#ffffff",
            "background": "#0f0f23",
        },
        "fonts": {
            "heading": "Montserrat",
            "heading_weight": "Bold",
            "heading_size": 36,
            "body": "Open Sans",
            "body_size": 18,
        },
    }


def _escape_xml(text: str) -> str:
    """Escape text for SVG/XML."""
    return (text
            .replace("&", "&")
            .replace("<", "<")
            .replace(">", ">")
            .replace('"', """)
            .replace("'", "'"))


def _wrap_text(text: str, max_chars: int = 60) -> list:
    """Wrap text into lines."""
    words = text.split()
    lines = []
    current = ""
    for word in words:
        if len(current) + len(word) + 1 > max_chars:
            if current:
                lines.append(current)
            current = word
        else:
            current = f"{current} {word}".strip()
    if current:
        lines.append(current)
    return lines


def _generate_title_slide(title: str, content: str, style: dict, img_path: str = None) -> str:
    """Generate a title/cover slide SVG."""
    colors = style.get("colors", {})
    fonts = style.get("fonts", {})
    bg = colors.get("background", "#0f0f23")
    accent = colors.get("accent", "#4a90d9")
    text_color = colors.get("text", "#ffffff")
    heading_font = fonts.get("heading", "Montserrat")
    body_font = fonts.get("body", "Open Sans")

    title_lines = _wrap_text(title, 30)
    title_y = 380

    tspan_lines = ""
    for i, line in enumerate(title_lines):
        tspan_lines += f'<tspan x="960" dy="{50 if i > 0 else 0}">{_escape_xml(line)}</tspan>'

    subtitle_text = _escape_xml(content[:100]) if content else ""

    # Background image or gradient
    bg_rect = f'<rect width="{CANVAS_W}" height="{CANVAS_H}" fill="{bg}"/>'
    if img_path:
        bg_rect = f'''<defs>
    <clipPath id="bgClip"><rect width="{CANVAS_W}" height="{CANVAS_H}" rx="0"/></clipPath>
</defs>
<image href="file:///{img_path}" x="0" y="0" width="{CANVAS_W}" height="{CANVAS_H}" 
       clip-path="url(#bgClip)" preserveAspectRatio="xMidYMid slice" opacity="0.3"/>
<rect width="{CANVAS_W}" height="{CANVAS_H}" fill="{bg}" opacity="0.7"/>'''

    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {CANVAS_W} {CANVAS_H}" width="{CANVAS_W}" height="{CANVAS_H}">
  <g id="slide_01">
    {bg_rect}
    <!-- Accent line -->
    <rect x="860" y="340" width="200" height="4" rx="2" fill="{accent}"/>
    <!-- Title -->
    <text x="960" y="{title_y}" text-anchor="middle" 
          font-family="{heading_font}" font-weight="Bold" font-size="52" fill="{text_color}">
      {tspan_lines}
    </text>
    <!-- Subtitle -->
    <text x="960" y="{title_y + len(title_lines) * 55 + 30}" text-anchor="middle" 
          font-family="{body_font}" font-size="22" fill="{text_color}" opacity="0.7">
      {_escape_xml(subtitle_text)}
    </text>
    <!-- Bottom accent -->
    <rect x="0" y="1060" width="{CANVAS_W}" height="20" fill="{accent}" opacity="0.8"/>
  </g>
</svg>'''


def _generate_content_slide(title: str, content: str, bullet_points: list, style: dict, img_path: str = None, slide_num: int = 1) -> str:
    """Generate a content slide SVG."""
    colors = style.get("colors", {})
    fonts = style.get("fonts", {})
    bg = colors.get("background", "#0f0f23")
    primary = colors.get("primary", "#1a1a2e")
    accent = colors.get("accent", "#4a90d9")
    text_color = colors.get("text", "#ffffff")
    heading_font = fonts.get("heading", "Montserrat")
    body_font = fonts.get("body", "Open Sans")
    heading_size = fonts.get("heading_size", 36)
    body_size = fonts.get("body_size", 18)

    # Build bullet points
    bullets = bullet_points if bullet_points else _extract_bullets(content)
    if not bullets:
        bullets = _wrap_text(content, 80)[:8]

    bullet_svg = ""
    start_y = 280
    for i, bp in enumerate(bullets[:8]):
        lines = _wrap_text(bp, 70)
        for j, line in enumerate(lines):
            y = start_y + i * 90 + j * 28
            if j == 0:
                bullet_svg += f'''    <circle cx="200" cy="{y - 6}" r="5" fill="{accent}"/>
    <text x="220" y="{y}" font-family="{body_font}" font-size="{body_size}" fill="{text_color}">
      {_escape_xml(line)}
    </text>
'''
            else:
                bullet_svg += f'''    <text x="220" y="{y}" font-family="{body_font}" font-size="{body_size}" fill="{text_color}" opacity="0.9">
      {_escape_xml(line)}
    </text>
'''

    # Image section (right side)
    image_svg = ""
    if img_path:
        image_svg = f'''    <!-- Image -->
    <defs><clipPath id="imgClip{slide_num}"><rect x="1200" y="200" width="600" height="680" rx="12"/></clipPath></defs>
    <image href="file:///{img_path}" x="1200" y="200" width="600" height="680" 
           clip-path="url(#imgClip{slide_num})" preserveAspectRatio="xMidYMid slice"/>
    <rect x="1200" y="200" width="600" height="680" rx="12" fill="none" stroke="{accent}" stroke-width="2" opacity="0.3"/>
'''

    # Slide number
    slide_num_display = f"{slide_num:02d}"

    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {CANVAS_W} {CANVAS_H}" width="{CANVAS_W}" height="{CANVAS_H}">
  <g id="slide_{slide_num_display}">
    <!-- Background -->
    <rect width="{CANVAS_W}" height="{CANVAS_H}" fill="{bg}"/>
    <!-- Top bar -->
    <rect x="0" y="0" width="{CANVAS_W}" height="6" fill="{accent}"/>
    <!-- Title -->
    <text x="120" y="120" font-family="{heading_font}" font-weight="Bold" font-size="{heading_size}" fill="{text_color}">
      {_escape_xml(title[:60])}
    </text>
    <!-- Title underline -->
    <rect x="120" y="140" width="300" height="3" rx="1" fill="{accent}"/>
    <!-- Bullets -->
{bullet_svg}
{image_svg}
    <!-- Slide number -->
    <text x="1860" y="1050" text-anchor="end" font-family="{body_font}" font-size="14" fill="{text_color}" opacity="0.4">
      {slide_num_display}
    </text>
  </g>
</svg>'''


def _generate_closing_slide(title: str, content: str, style: dict) -> str:
    """Generate a closing/thank you slide SVG."""
    colors = style.get("colors", {})
    fonts = style.get("fonts", {})
    bg = colors.get("background", "#0f0f23")
    accent = colors.get("accent", "#4a90d9")
    text_color = colors.get("text", "#ffffff")
    heading_font = fonts.get("heading", "Montserrat")

    text = title if title else "Cảm ơn bạn đã theo dõi!"
    subtitle = content[:80] if content else ""

    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {CANVAS_W} {CANVAS_H}" width="{CANVAS_W}" height="{CANVAS_H}">
  <g id="slide_closing">
    <rect width="{CANVAS_W}" height="{CANVAS_H}" fill="{bg}"/>
    <rect x="0" y="0" width="{CANVAS_W}" height="6" fill="{accent}"/>
    <rect x="0" y="1074" width="{CANVAS_W}" height="6" fill="{accent}"/>
    <text x="960" y="480" text-anchor="middle" font-family="{heading_font}" font-weight="Bold" font-size="52" fill="{text_color}">
      {_escape_xml(text)}
    </text>
    <text x="960" y="550" text-anchor="middle" font-family="{heading_font}" font-size="22" fill="{text_color}" opacity="0.6">
      {_escape_xml(subtitle)}
    </text>
    <rect x="810" y="580" width="300" height="3" rx="1" fill="{accent}"/>
  </g>
</svg>'''


def _extract_bullets(content: str) -> list:
    """Extract bullet points from content text."""
    bullets = []
    for line in content.split("\n"):
        line = line.strip()
        if line.startswith("- ") or line.startswith("* ") or line.startswith("• "):
            bullets.append(line[2:].strip())
        elif line.startswith("– ") or line.startswith("— "):
            bullets.append(line[2:].strip())
    return bullets[:8]


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Assemble slides into SVG and PPTX")
    parser.add_argument("project_path", help="Project directory")
    args = parser.parse_args()

    project_path = Path(args.project_path)
    if not project_path.exists():
        print(f"Error: Directory not found: {project_path}", file=sys.stderr)
        return 1

    result = assemble(project_path)
    print(f"\n[Done] {result['total_slides']} slides assembled")
    print(f"[Done] SVG: {result['svg_dir']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
