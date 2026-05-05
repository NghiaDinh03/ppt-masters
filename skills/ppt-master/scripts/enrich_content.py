#!/usr/bin/env python3
"""
Enrich Content — AI diễn giải chi tiết nội dung từng slide

Input: sources/slide_metadata.json
Output: slides_enriched.json

Usage:
    python3 enrich_content.py <project_path> [--llm openclaude|ollama]
"""

import sys
import os
import json
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))


def enrich_slides(project_path: Path, llm_provider: str = "openclaude") -> list:
    """Enrich all slides with detailed content using LLM.

    Args:
        project_path: Project directory containing sources/slide_metadata.json
        llm_provider: LLM provider to use ("openclaude" or "ollama")

    Returns:
        List of enriched slide dicts.
    """
    # Read metadata
    metadata_path = project_path / "sources" / "slide_metadata.json"
    if not metadata_path.exists():
        # Try alternative locations
        for alt in ["slide_metadata.json", "slides_structured.json"]:
            alt_path = project_path / alt
            if alt_path.exists():
                metadata_path = alt_path
                break
        else:
            raise FileNotFoundError(f"slide_metadata.json not found in {project_path}")

    slides = json.loads(metadata_path.read_text(encoding="utf-8"))
    print(f"[enrich] Processing {len(slides)} slides with {llm_provider}...")

    enriched_slides = []

    if llm_provider == "openclaude":
        from llm_backends.backend_openclaude import enrich_slide_content
        for i, slide in enumerate(slides):
            print(f"[enrich] Slide {i+1}/{len(slides)}: {slide.get('title', '?')[:50]}...")
            enriched = enrich_slide_content(slide)
            enriched_slides.append(enriched)
    elif llm_provider == "ollama":
        enriched_slides = _enrich_with_ollama(slides, project_path)
    else:
        # No LLM — pass through with basic enrichment
        for slide in slides:
            enriched_slides.append({
                **slide,
                "content": slide.get("content_raw", ""),
                "bullet_points": [],
                "enriched": False,
                "image_hint": f"hình ảnh liên quan đến {slide.get('title', '')}",
            })

    # Save enriched data
    output_path = project_path / "slides_enriched.json"
    output_path.write_text(json.dumps(enriched_slides, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[enrich] Saved: {output_path}")

    # Also create per-slide folders
    slides_dir = project_path / "slides"
    slides_dir.mkdir(exist_ok=True)
    for slide in enriched_slides:
        num = slide.get("slide_number", 0)
        slide_dir = slides_dir / f"slide_{num:02d}"
        slide_dir.mkdir(exist_ok=True)
        (slide_dir / "content.json").write_text(
            json.dumps(slide, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        content_md = f"# {slide.get('title', 'Slide')}\n\n{slide.get('content', '')}\n"
        if slide.get("bullet_points"):
            content_md += "\n" + "\n".join(f"- {bp}" for bp in slide["bullet_points"])
        (slide_dir / "content.md").write_text(content_md, encoding="utf-8")

    return enriched_slides


def _enrich_with_ollama(slides: list, project_path: Path) -> list:
    """Enrich slides using local Ollama (Gemma4)."""
    import requests

    endpoint = os.environ.get("OLLAMA_ENDPOINT", "http://localhost:11434")
    model = os.environ.get("OLLAMA_MODEL", "gemma4:8b")

    enriched = []
    for slide in slides:
        content = slide.get("content_raw", "")
        title = slide.get("title", "")

        if not content.strip():
            enriched.append({**slide, "content": content, "bullet_points": [], "enriched": False, "image_hint": ""})
            continue

        prompt = f"""Bạn là chuyên gia giáo dục. Hãy DIỄN GIẢI chi tiết nội dung sau (KHÔNG tóm tắt):

Tiêu đề: {title}
Nội dung: {content[:2000]}

Trả về JSON:
{{"title": "...", "content": "nội dung chi tiết", "bullet_points": ["..."], "image_hint": "mô tả hình ảnh"}}"""

        try:
            resp = requests.post(
                f"{endpoint}/api/generate",
                json={"model": model, "prompt": prompt, "stream": False},
                timeout=120,
            )
            resp.raise_for_status()
            response_text = resp.json().get("response", "")

            # Parse JSON from response
            clean = response_text.strip()
            if "```" in clean:
                clean = clean.split("```")[1]
                if clean.startswith("json"):
                    clean = clean[4:]
            result = json.loads(clean.strip())
            result["enriched"] = True
            result["slide_number"] = slide.get("slide_number", 0)
            result["type"] = slide.get("type", "content")
            enriched.append(result)
        except Exception as e:
            print(f"[ollama] Failed for slide {slide.get('slide_number', '?')}: {e}")
            enriched.append({
                **slide, "content": content, "bullet_points": [],
                "enriched": False, "image_hint": f"hình ảnh liên quan đến {title}",
            })

    return enriched


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Enrich slide content with AI")
    parser.add_argument("project_path", help="Project directory")
    parser.add_argument("--llm", default="openclaude", choices=["openclaude", "ollama", "none"],
                        help="LLM provider (default: openclaude)")
    args = parser.parse_args()

    project_path = Path(args.project_path)
    if not project_path.exists():
        print(f"Error: Directory not found: {project_path}", file=sys.stderr)
        return 1

    enrich_slides(project_path, args.llm)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
