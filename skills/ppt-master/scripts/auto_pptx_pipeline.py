#!/usr/bin/env python3
"""
Auto PPTX Pipeline — 1 command chạy toàn bộ pipeline

Input: File PPTX/DOCX/PDF + style prompt
Output: PPTX editable + per-slide folders

Usage:
    python3 auto_pptx_pipeline.py <input_file> \\
        --style "[title] Giáo dục [style] nền galaxy, màu đen chủ đạo" \\
        --image-mode auto \\
        --llm openclaude \\
        --tts edge \\
        --output-dir projects/my_presentation
"""

import sys
import os
import json
import time
from pathlib import Path


# Windows console encoding fix
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))


def run_pipeline(
    input_file: str,
    style_prompt: str = "",
    image_mode: str = "auto",
    llm_provider: str = "openclaude",
    tts_provider: str = "edge",
    tts_voice: str = None,
    output_dir: str = None,
    skip_audio: bool = False,
) -> dict:
    """Run the full PPTX generation pipeline.

    Args:
        input_file: Path to input document (PPTX/DOCX/PDF)
        style_prompt: User style prompt string
        image_mode: Image acquisition mode ("search", "pollinations", "auto")
        llm_provider: LLM provider for content enrichment
        tts_provider: TTS provider for audio generation
        tts_voice: Voice name/ID for TTS
        output_dir: Output directory
        skip_audio: Skip audio generation

    Returns:
        Pipeline result dict.
    """
    start_time = time.time()
    input_path = Path(input_file)

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")

    # Determine output directory
    if output_dir:
        project_path = Path(output_dir)
    else:
        project_name = input_path.stem.replace(" ", "_")[:30]
        project_path = Path("projects") / project_name

    project_path.mkdir(parents=True, exist_ok=True)
    sources_dir = project_path / "sources"
    sources_dir.mkdir(exist_ok=True)

    # Copy input file to sources
    import shutil
    shutil.copy2(str(input_path), str(sources_dir / input_path.name))

    print("=" * 60)
    print(f"  PPT Master — Auto Pipeline")
    print(f"  Input: {input_path.name}")
    print(f"  Output: {project_path}")
    print("=" * 60)

    # ── Step 1: Extract slide assets ──
    print("\n[Step 1/7] Extracting slide content + images...")
    from extract_slide_assets import extract_from_pptx, extract_from_docx, extract_from_pdf

    suffix = input_path.suffix.lower()
    if suffix == ".pptx":
        extract_result = extract_from_pptx(input_path, sources_dir)
    elif suffix == ".pdf":
        extract_result = extract_from_pdf(input_path, sources_dir)
    else:
        extract_result = extract_from_docx(input_path, sources_dir)

    print(f"  -> {extract_result['total_slides']} slides extracted")

    # ── Step 1.5: OCR images (extract text from embedded images) ──
    print("\n[Step 1.5/7] OCR on extracted images...")
    try:
        from ocr_slide_images import ocr_slide_images
        ocr_result = ocr_slide_images(project_path)
        print(f"  -> {ocr_result.get('ocr_count', 0)} images OCR processed")
    except Exception as e:
        print(f"  -> OCR skipped: {str(e)[:80]}")

    # ── Step 2: Parse style prompt ──
    print("\n[Step 2/6] Parsing style prompt...")
    from parse_style_prompt import parse_style_prompt

    if style_prompt:
        style_config = parse_style_prompt(style_prompt)
    else:
        style_config = parse_style_prompt("[title] Presentation [style] hiện đại, xanh dương")

    style_path = project_path / "style_config.json"
    style_path.write_text(json.dumps(style_config, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  -> Style: {style_config.get('title', 'Default')}")

    # ── Step 3: Vision + Text AI analysis (2-pass) ──
    print(f"\n[Step 3/7] Vision + Text AI analysis ({llm_provider})...")
    try:
        from vision_analyze_slides import vision_analyze_slides
        vision_result = vision_analyze_slides(project_path, llm_provider)
        print(f"  -> {vision_result.get('vision_count', 0)} slides with vision analysis")
        print(f"  -> {vision_result.get('enriched_count', 0)} slides enriched")
    except Exception as e:
        print(f"  -> Vision analysis failed: {e}")
        print(f"  -> Falling back to basic enrichment...")
        try:
            from enrich_content import enrich_slides
            enrich_slides(project_path, llm_provider)
        except Exception as e2:
            print(f"  -> Basic enrichment also failed: {e2}")
            # Create enriched from metadata
            metadata = json.loads((sources_dir / "slide_metadata.json").read_text(encoding="utf-8"))
            enriched = []
            for slide in metadata:
                enriched.append({
                    **slide,
                    "content": slide.get("content_raw", ""),
                    "bullet_points": [],
                    "enriched": False,
                    "image_hint": f"hinh anh lien quan den {slide.get('title', '')}",
                })
            enriched_path = project_path / "slides_enriched.json"
            enriched_path.write_text(json.dumps(enriched, ensure_ascii=False, indent=2), encoding="utf-8")

            slides_dir = project_path / "slides"
            slides_dir.mkdir(exist_ok=True)
        for slide in enriched:
            num = slide.get("slide_number", 0)
            slide_dir = slides_dir / f"slide_{num:02d}"
            slide_dir.mkdir(exist_ok=True)
            (slide_dir / "content.json").write_text(json.dumps(slide, ensure_ascii=False, indent=2), encoding="utf-8")

    # ── Step 4: Generate/search images ──
    print(f"\n[Step 4/6] Processing images (mode={image_mode})...")
    from slide_image_pipeline import process_slide_images

    try:
        image_mapping = process_slide_images(project_path, image_mode)
        total_images = sum(len(v) for v in image_mapping.values())
        print(f"  -> {total_images} images acquired")
    except Exception as e:
        print(f"  -> Image pipeline failed: {e}")
        print(f"  -> Continuing without images")

    # ── Step 5: Assemble slides -> SVG -> PPTX ──
    print("\n[Step 5/6] Assembling slides...")
    from assemble_slides import assemble

    try:
        assemble_result = assemble(project_path)
        print(f"  -> {assemble_result['total_slides']} SVG slides generated")
    except Exception as e:
        print(f"  -> Assembly failed: {e}")
        return {"status": "error", "error": str(e), "project_path": str(project_path)}

    # ── Step 6: Audio (optional) ──
    if not skip_audio and tts_provider:
        print(f"\n[Step 6/6] Generating audio (provider={tts_provider})...")
        from slide_audio_pipeline import generate_slide_audio

        try:
            audio_mapping = generate_slide_audio(project_path, tts_provider, voice=tts_voice)
            print(f"  -> {len(audio_mapping)} audio files generated")
        except Exception as e:
            print(f"  -> Audio generation failed: {e}")
    else:
        print("\n[Step 6/6] Audio generation skipped")

    # ── Summary ──
    elapsed = time.time() - start_time
    print("\n" + "=" * 60)
    print(f"  Pipeline Complete!")
    print(f"  Time: {elapsed:.1f}s")
    print(f"  Project: {project_path}")
    print(f"  Slides: {len(enriched)}")

    # Find PPTX output
    pptx_files = list(project_path.rglob("*.pptx"))
    if pptx_files:
        print(f"  PPTX: {pptx_files[0]}")
    print("=" * 60)

    return {
        "status": "success",
        "project_path": str(project_path),
        "total_slides": len(enriched),
        "elapsed_seconds": round(elapsed, 1),
        "pptx_path": str(pptx_files[0]) if pptx_files else None,
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Auto PPTX Pipeline — 1 command to generate PPTX")
    parser.add_argument("input_file", help="Input file (PPTX/DOCX/PDF)")
    parser.add_argument("--style", default="", help="Style prompt (e.g. '[title] Giáo dục [style] nền galaxy')")
    parser.add_argument("--image-mode", default="auto", choices=["search", "pollinations", "auto"],
                        help="Image mode (default: auto)")
    parser.add_argument("--llm", default="openclaude", choices=["openclaude", "ollama", "none"],
                        help="LLM provider (default: openclaude)")
    parser.add_argument("--tts", default="edge", choices=["edge", "elevenlabs", "minimax", "qwen", "cosyvoice", "none"],
                        help="TTS provider (default: edge)")
    parser.add_argument("--tts-voice", default=None, help="TTS voice name/ID")
    parser.add_argument("--output-dir", default=None, help="Output directory")
    parser.add_argument("--skip-audio", action="store_true", help="Skip audio generation")
    args = parser.parse_args()

    result = run_pipeline(
        input_file=args.input_file,
        style_prompt=args.style,
        image_mode=args.image_mode,
        llm_provider=args.llm,
        tts_provider=args.tts if args.tts != "none" else None,
        tts_voice=args.tts_voice,
        output_dir=args.output_dir,
        skip_audio=args.skip_audio,
    )

    if result["status"] == "error":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
