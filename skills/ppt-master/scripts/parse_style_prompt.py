#!/usr/bin/env python3
"""
Parse Style Prompt — Parse user style prompt into config JSON

Input: User prompt string (e.g. "[title] Giáo dục [style] nền galaxy, màu đen chủ đạo")
Output: style_config.json

Usage:
    python3 parse_style_prompt.py "[title] Giáo dục [style] nền galaxy" -o projects/my_ppt/style_config.json
"""

import sys
import os
import json
import re
from pathlib import Path


# Windows console encoding fix
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))


# Default style config
DEFAULT_STYLE = {
    "title": "Presentation",
    "colors": {
        "primary": "#1a1a2e",
        "secondary": "#16213e",
        "accent": "#4a90d9",
        "text": "#ffffff",
        "background": "#0f0f23",
        "background_gradient": "linear-gradient(135deg, #0f0f23 0%, #1a1a2e 50%, #16213e 100%)",
    },
    "fonts": {
        "heading": "Montserrat",
        "heading_weight": "Bold",
        "heading_size": 36,
        "body": "Open Sans",
        "body_size": 18,
    },
    "layout": {
        "cover": "full_image",
        "content": "two_column",
        "closing": "centered",
    },
    "icons": "flat_line",
    "image_search": "",
    "language": "vi",
    "page_count": {"min": 8, "max": 10},
}


# Color name mapping
COLOR_MAP = {
    "đen": "#000000", "black": "#000000",
    "trắng": "#ffffff", "white": "#ffffff",
    "xanh dương": "#1a73e8", "blue": "#1a73e8",
    "xanh lá": "#34a853", "green": "#34a853",
    "đỏ": "#ea4335", "red": "#ea4335",
    "vàng": "#fbbc04", "yellow": "#fbbc04",
    "tím": "#9c27b0", "purple": "#9c27b0",
    "cam": "#ff6d00", "orange": "#ff6d00",
    "hồng": "#e91e63", "pink": "#e91e63",
    "xám": "#9e9e9e", "gray": "#9e9e9e", "grey": "#9e9e9e",
    "xanh navy": "#1a1a2e", "navy": "#1a1a2e",
    "xanh đậm": "#0d47a1", "dark blue": "#0d47a1",
    "gradient galaxy": "galaxy",
    "nền galaxy": "galaxy",
    "galaxy": "galaxy",
}

GALAXY_GRADIENT = "linear-gradient(135deg, #0f0f23 0%, #1a1a2e 30%, #2d1b69 60%, #0f0f23 100%)"


def parse_style_prompt(prompt: str) -> dict:
    """Parse a style prompt into a config dict.

    Supports tagged format: [title]... [style]... [font]... [layout]...
    Also supports natural language (best effort).
    """
    config = json.loads(json.dumps(DEFAULT_STYLE))  # Deep copy

    # Extract tagged sections
    tags = {}
    tag_pattern = r"\[(\w+)\]\s*(.*?)(?=\[|\Z)"
    matches = re.findall(tag_pattern, prompt, re.DOTALL | re.IGNORECASE)
    for tag, value in matches:
        tags[tag.lower()] = value.strip()

    # If no tags found, try natural language parsing
    if not tags:
        tags = _parse_natural_language(prompt)

    # Apply tags to config
    if "title" in tags:
        config["title"] = tags["title"]

    if "style" in tags:
        _apply_style(config, tags["style"])

    if "font" in tags:
        _apply_font(config, tags["font"])

    if "layout" in tags:
        config["layout"]["content"] = _parse_layout(tags["layout"])

    if "icon" in tags:
        config["icons"] = _parse_icon_style(tags["icon"])

    if "image" in tags:
        config["image_search"] = tags["image"]

    if "language" in tags:
        lang = tags["language"].lower()
        if "việt" in lang or "viet" in lang or lang == "vi":
            config["language"] = "vi"
        elif "eng" in lang or lang == "en":
            config["language"] = "en"
        elif "trung" in lang or "china" in lang or lang == "zh":
            config["language"] = "zh"

    if "pages" in tags:
        _apply_page_count(config, tags["pages"])

    return config


def _parse_natural_language(prompt: str) -> dict:
    """Best-effort parse of natural language style description."""
    tags = {}
    prompt_lower = prompt.lower()

    # Extract title (first sentence or up to first comma)
    title_match = re.search(r"(?:về|about|about)\s+(.+?)(?:,|\.|$)", prompt, re.IGNORECASE)
    if title_match:
        tags["title"] = title_match.group(1).strip()

    # Extract colors
    for color_name, color_hex in COLOR_MAP.items():
        if color_name in prompt_lower:
            if "style" not in tags:
                tags["style"] = ""
            tags["style"] += f" {color_name}"

    # Extract page count
    page_match = re.search(r"(\d+)\s*(?:slide|trang|page)", prompt, re.IGNORECASE)
    if page_match:
        tags["pages"] = page_match.group(1)

    return tags


def _apply_style(config: dict, style_text: str):
    """Apply style description to config."""
    style_lower = style_text.lower()

    # Find primary color
    for color_name, color_hex in COLOR_MAP.items():
        if color_name in style_lower:
            if color_hex == "galaxy":
                config["colors"]["background_gradient"] = GALAXY_GRADIENT
                config["colors"]["background"] = "#0f0f23"
                config["colors"]["primary"] = "#1a1a2e"
            else:
                if "chủ đạo" in style_lower or "primary" in style_lower:
                    config["colors"]["primary"] = color_hex
                elif "accent" in style_lower:
                    config["colors"]["accent"] = color_hex
                else:
                    config["colors"]["primary"] = color_hex

    # Detect theme keywords
    if "hiện đại" in style_lower or "modern" in style_lower:
        config["fonts"]["heading"] = "Montserrat"
        config["fonts"]["body"] = "Open Sans"
    elif "cổ điển" in style_lower or "classic" in style_lower:
        config["fonts"]["heading"] = "Times New Roman"
        config["fonts"]["body"] = "Georgia"
    elif "tối giản" in style_lower or "minimal" in style_lower:
        config["fonts"]["heading"] = "Helvetica"
        config["fonts"]["body"] = "Arial"
        config["colors"]["background"] = "#ffffff"
        config["colors"]["text"] = "#333333"


def _apply_font(config: dict, font_text: str):
    """Apply font description to config."""
    # Try to extract font name and size
    size_match = re.search(r"(\d+)\s*(?:pt|px)", font_text)
    if size_match:
        config["fonts"]["heading_size"] = int(size_match.group(1))

    # Common font names
    fonts = ["Montserrat", "Roboto", "Open Sans", "Poppins", "Inter", "Arial",
             "Times New Roman", "Georgia", "Helvetica", "Lato"]
    for font in fonts:
        if font.lower() in font_text.lower():
            config["fonts"]["heading"] = font
            break


def _parse_layout(layout_text: str) -> str:
    """Parse layout description."""
    lt = layout_text.lower()
    if "2 cột" in lt or "two column" in lt or "chia" in lt:
        return "two_column"
    elif "full" in lt or "toàn" in lt:
        return "full_image"
    elif "trái" in lt or "left" in lt:
        return "image_left"
    elif "phải" in lt or "right" in lt:
        return "image_right"
    return "two_column"


def _parse_icon_style(icon_text: str) -> str:
    """Parse icon style."""
    it = icon_text.lower()
    if "line" in it or "viền" in it:
        return "flat_line"
    elif "fill" in it or "đậm" in it:
        return "filled"
    elif "duotone" in it:
        return "duotone"
    return "flat_line"


def _apply_page_count(config: dict, pages_text: str):
    """Apply page count from text."""
    numbers = re.findall(r"\d+", pages_text)
    if len(numbers) >= 2:
        config["page_count"] = {"min": int(numbers[0]), "max": int(numbers[1])}
    elif len(numbers) == 1:
        n = int(numbers[0])
        config["page_count"] = {"min": max(1, n - 2), "max": n + 2}


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Parse style prompt to config JSON")
    parser.add_argument("prompt", help="Style prompt string")
    parser.add_argument("-o", "--output", default=None, help="Output file path")
    args = parser.parse_args()

    config = parse_style_prompt(args.prompt)

    output_json = json.dumps(config, ensure_ascii=False, indent=2)

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(output_json, encoding="utf-8")
        print(f"[OK] Saved: {output_path}")
    else:
        print(output_json)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
