#!/usr/bin/env python3
"""
Slide Image Pipeline — Auto gen/search hình ảnh cho từng slide

Input: slides_enriched.json
Output: slides/slide_XX/images/

Usage:
    python3 slide_image_pipeline.py <project_path> --mode search|pollinations|auto
"""

import sys
import os
import json
import subprocess
from pathlib import Path


# Windows console encoding fix
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))


def process_slide_images(project_path: Path, mode: str = "auto") -> dict:
    """Generate or search images for each slide.

    Args:
        project_path: Project directory with slides_enriched.json
        mode: "search" (Pexels/Pixabay), "pollinations" (free AI), "auto"

    Returns:
        Image mapping dict.
    """
    enriched_path = project_path / "slides_enriched.json"
    if not enriched_path.exists():
        raise FileNotFoundError(f"slides_enriched.json not found in {project_path}")

    slides = json.loads(enriched_path.read_text(encoding="utf-8"))
    print(f"[images] Processing {len(slides)} slides, mode={mode}")

    image_mapping = {}
    scripts_dir = Path(__file__).resolve().parent

    for slide in slides:
        num = slide.get("slide_number", 0)
        slide_dir = project_path / "slides" / f"slide_{num:02d}"
        images_dir = slide_dir / "images"
        images_dir.mkdir(parents=True, exist_ok=True)

        # Get image hint from enriched data
        image_hint = slide.get("image_hint", "")
        if not image_hint:
            image_hint = f"hình ảnh liên quan đến {slide.get('title', 'slide')}"

        print(f"[images] Slide {num}: {image_hint[:60]}...")

        image_files = []
        slide_mode = mode

        if slide_mode == "auto":
            # Try search first, fallback to pollinations
            slide_mode = "search"

        if slide_mode == "search":
            try:
                result = _search_image(scripts_dir, image_hint, images_dir, num)
                if result:
                    image_files.append(result)
                    print(f"[images]   Found via search: {result}")
                else:
                    print(f"[images]   Search returned nothing, trying pollinations...")
                    result = _generate_pollinations(image_hint, images_dir, num)
                    if result:
                        image_files.append(result)
            except Exception as e:
                print(f"[images]   Search failed: {e}, trying pollinations...")
                result = _generate_pollinations(image_hint, images_dir, num)
                if result:
                    image_files.append(result)

        elif slide_mode == "pollinations":
            result = _generate_pollinations(image_hint, images_dir, num)
            if result:
                image_files.append(result)

        image_mapping[f"slide_{num:02d}"] = image_files

    # Save mapping
    mapping_path = project_path / "image_mapping.json"
    mapping_path.write_text(json.dumps(image_mapping, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[images] Saved mapping: {mapping_path}")

    return image_mapping


def _search_image(scripts_dir: Path, query: str, output_dir: Path, slide_num: int) -> str:
    """Search for an image using image_search.py."""
    script = scripts_dir / "image_search.py"
    if not script.exists():
        return None

    filename = f"slide_{slide_num:02d}_bg.jpg"
    try:
        result = subprocess.run(
            [sys.executable, str(script), query,
             "--filename", filename,
             "--orientation", "landscape",
             "-o", str(output_dir)],
            capture_output=True, text=True, timeout=60,
            cwd=str(scripts_dir.parent.parent),
        )
        output_path = output_dir / filename
        if output_path.exists():
            return filename
    except Exception as e:
        print(f"[images]   search error: {e}")
    return None


def _generate_pollinations(prompt: str, output_dir: Path, slide_num: int) -> str:
    """Generate image using Pollinations.ai (free)."""
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from image_backends.backend_pollinations import generate

        filename = f"slide_{slide_num:02d}_bg.jpg"
        output_path = output_dir / filename
        generate(prompt, str(output_path), aspect_ratio="16:9", image_size="1K")
        return filename
    except Exception as e:
        print(f"[images]   pollinations error: {e}")
    return None


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Slide image pipeline")
    parser.add_argument("project_path", help="Project directory")
    parser.add_argument("--mode", default="auto", choices=["search", "pollinations", "auto"],
                        help="Image acquisition mode (default: auto)")
    args = parser.parse_args()

    project_path = Path(args.project_path)
    if not project_path.exists():
        print(f"Error: Directory not found: {project_path}", file=sys.stderr)
        return 1

    process_slide_images(project_path, args.mode)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
