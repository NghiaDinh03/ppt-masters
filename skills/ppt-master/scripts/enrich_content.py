#!/usr/bin/env python3
"""
Enrich Content v2 — AI diễn giải chi tiết nội dung từng slide

Cải tiến:
- Xử lý "request blocked" gracefully
- Fallback: giữ nguyên content gốc khi LLM fail
- Chi tiết log cho từng step
- Hỗ trợ batch processing để giảm API calls

Usage:
    python3 enrich_content.py <project_path> [--llm openclaude|ollama|none]
"""

import sys
import os
import json
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

# Windows console encoding fix
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def enrich_slides(project_path: Path, llm_provider: str = "openclaude") -> list:
    """Enrich all slides with detailed content using LLM.

    Args:
        project_path: Project directory containing sources/slide_metadata.json
        llm_provider: LLM provider to use ("openclaude", "ollama", "none")

    Returns:
        List of enriched slide dicts.
    """
    # Read metadata
    metadata_path = project_path / "sources" / "slide_metadata.json"
    if not metadata_path.exists():
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
    success_count = 0
    fail_count = 0

    if llm_provider == "none":
        # No LLM — pass through with basic enrichment
        for slide in slides:
            enriched_slides.append(_basic_enrich(slide))
        print(f"[enrich] No LLM — used raw content for all slides")
    elif llm_provider == "openclaude":
        enriched_slides, success_count, fail_count = _enrich_with_openclaude(slides)
    elif llm_provider == "ollama":
        enriched_slides, success_count, fail_count = _enrich_with_ollama(slides, project_path)
    else:
        for slide in slides:
            enriched_slides.append(_basic_enrich(slide))

    # Save enriched data
    output_path = project_path / "slides_enriched.json"
    output_path.write_text(json.dumps(enriched_slides, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[enrich] Saved: {output_path}")
    print(f"[enrich] Results: {success_count} enriched, {fail_count} fallback to raw content")

    # Create per-slide folders
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
        if slide.get("table_data"):
            content_md += "\n\n### Data:\n" + "\n".join(slide["table_data"])
        (slide_dir / "content.md").write_text(content_md, encoding="utf-8")

    return enriched_slides


def _basic_enrich(slide: dict) -> dict:
    """Basic enrichment without LLM — use raw content."""
    title = slide.get("title", "")
    content = slide.get("content_raw", "")
    bullet_points = slide.get("bullet_points", [])
    table_data = slide.get("table_data", [])

    # Extract bullets from content if not already present
    if not bullet_points:
        for line in content.split("\n"):
            line = line.strip()
            if line.startswith("- ") or line.startswith("* ") or line.startswith("  "):
                bullet_points.append(line.strip())

    return {
        "slide_number": slide.get("slide_number", 0),
        "type": slide.get("layout_hint", "content"),
        "title": title,
        "content": content,
        "bullet_points": bullet_points,
        "table_data": table_data,
        "enriched": False,
        "image_hint": f"hinh anh lien quan den {title}",
    }


def _enrich_with_openclaude(slides: list) -> tuple:
    """Enrich slides using Open Claude with error handling."""
    try:
        from llm_backends.backend_openclaude import enrich_slide_content, chat_completion
    except ImportError as e:
        print(f"[enrich] ERROR: Cannot import Open Claude backend: {e}")
        enriched = [_basic_enrich(s) for s in slides]
        return enriched, 0, len(slides)

    # Test connection first
    print(f"[enrich] Testing Open Claude connection...")
    try:
        test = chat_completion("Say OK", max_tokens=10, temperature=0)
        print(f"[enrich] Connection OK: {test[:20]}")
    except Exception as e:
        print(f"[enrich] Connection failed: {e}")
        print(f"[enrich] Falling back to raw content for all slides")
        enriched = [_basic_enrich(s) for s in slides]
        return enriched, 0, len(slides)

    enriched_slides = []
    success_count = 0
    fail_count = 0
    blocked_count = 0

    for i, slide in enumerate(slides):
        title = slide.get("title", "?")
        content = slide.get("content_raw", "")

        print(f"[enrich] Slide {i+1}/{len(slides)}: {title[:50]}...")

        # Skip empty slides
        if not content.strip() or len(content.strip()) < 10:
            print(f"[enrich]   Skipped (too short)")
            enriched_slides.append(_basic_enrich(slide))
            continue

        # Try to enrich
        try:
            enriched = enrich_slide_content(slide)
            if enriched.get("enriched"):
                success_count += 1
                print(f"[enrich]   OK - enriched ({len(enriched.get('content', ''))} chars)")
            else:
                fail_count += 1
                print(f"[enrich]   Fallback - used raw content")
            enriched_slides.append(enriched)
        except Exception as e:
            error_msg = str(e)
            if "blocked" in error_msg.lower() or "403" in error_msg:
                blocked_count += 1
                if blocked_count <= 3:
                    print(f"[enrich]   BLOCKED by content filter: {error_msg[:80]}")
                elif blocked_count == 4:
                    print(f"[enrich]   BLOCKED - switching to no-LLM mode for remaining slides")
                    # Fill remaining with basic enrich
                    enriched_slides.append(_basic_enrich(slide))
                    for remaining in slides[i+1:]:
                        enriched_slides.append(_basic_enrich(remaining))
                    fail_count += len(slides) - i
                    break
            else:
                fail_count += 1
                print(f"[enrich]   ERROR: {error_msg[:80]}")
            enriched_slides.append(_basic_enrich(slide))

    if blocked_count > 0:
        print(f"[enrich] WARNING: {blocked_count} slides blocked by content filter")
        print(f"[enrich] TIP: Try --llm none to skip enrichment, or use --llm ollama for local processing")

    return enriched_slides, success_count, fail_count


def _enrich_with_ollama(slides: list, project_path: Path) -> tuple:
    """Enrich slides using local Ollama."""
    import requests

    endpoint = os.environ.get("OLLAMA_ENDPOINT", "http://localhost:11434")
    model = os.environ.get("OLLAMA_MODEL", "gemma4:8b")

    enriched = []
    success_count = 0
    fail_count = 0

    for i, slide in enumerate(slides):
        content = slide.get("content_raw", "")
        title = slide.get("title", "")

        print(f"[enrich] Slide {i+1}/{len(slides)}: {title[:50]}...")

        if not content.strip() or len(content.strip()) < 10:
            enriched.append(_basic_enrich(slide))
            fail_count += 1
            continue

        prompt = f"""Ban la chuyen gia giao duc. Hay DIEN GIAI chi tiet noi dung sau (KHONG tom tat):

Tieu de: {title}
Noi dung: {content[:2000]}

Tra ve JSON:
{{"title": "...", "content": "noi dung chi tiet", "bullet_points": ["..."], "image_hint": "mo ta hinh anh"}}"""

        try:
            resp = requests.post(
                f"{endpoint}/api/generate",
                json={"model": model, "prompt": prompt, "stream": False},
                timeout=120,
            )
            resp.raise_for_status()
            response_text = resp.json().get("response", "")

            clean = response_text.strip()
            if "```" in clean:
                clean = clean.split("```")[1]
                if clean.startswith("json"):
                    clean = clean[4:]
            result = json.loads(clean.strip())
            result["enriched"] = True
            result["slide_number"] = slide.get("slide_number", 0)
            result["type"] = slide.get("layout_hint", "content")
            enriched.append(result)
            success_count += 1
            print(f"[enrich]   OK - enriched")
        except Exception as e:
            print(f"[enrich]   Failed: {str(e)[:60]}")
            enriched.append(_basic_enrich(slide))
            fail_count += 1

    return enriched, success_count, fail_count


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
