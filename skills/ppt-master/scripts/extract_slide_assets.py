#!/usr/bin/env python3
"""
Extract Slide Assets — Tách text + hình ảnh từ PPTX/DOCX/PDF

Input: File PPTX/DOCX/PDF
Output:
  - sources/extracted.md          (markdown content)
  - sources/images/               (extracted images)
  - sources/slide_metadata.json   (metadata per slide)

Usage:
    python3 extract_slide_assets.py <input_file> -o <output_dir>
"""

import sys
import os
import json
import re
import shutil
from pathlib import Path


# Windows console encoding fix
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))


def extract_from_pptx(input_path: Path, output_dir: Path) -> dict:
    """Extract text + images from PPTX file."""
    from pptx import Presentation
    from pptx.util import Inches

    prs = Presentation(str(input_path))
    images_dir = output_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    slides_data = []
    all_text = []

    for slide_idx, slide in enumerate(prs.slides, 1):
        slide_text = []
        slide_images = []

        # Extract text
        for shape in slide.shapes:
            if shape.has_text_frame:
                for para in shape.text_frame.paragraphs:
                    text = para.text.strip()
                    if text:
                        slide_text.append(text)

            # Extract images
            if shape.shape_type == 13:  # Picture
                image = shape.image
                ext = image.content_type.split("/")[-1]
                if ext == "jpeg":
                    ext = "jpg"
                img_name = f"slide_{slide_idx:02d}_image_{len(slide_images)+1:02d}.{ext}"
                img_path = images_dir / img_name
                with open(img_path, "wb") as f:
                    f.write(image.blob)
                slide_images.append(img_name)

        # Detect layout hint
        layout_hint = "content"
        if slide_idx == 1:
            layout_hint = "title_slide"
        elif len(slide_images) > 1:
            layout_hint = "image_heavy"
        elif not slide_text:
            layout_hint = "closing"

        title = slide_text[0] if slide_text else f"Slide {slide_idx}"
        content = "\n".join(slide_text)

        slides_data.append({
            "slide_number": slide_idx,
            "title": title,
            "content_raw": content,
            "images_extracted": slide_images,
            "layout_hint": layout_hint,
        })

        all_text.append(f"## Slide {slide_idx}: {title}\n\n{content}")

    # Write markdown
    md_content = "\n\n".join(all_text)
    (output_dir / "extracted.md").write_text(md_content, encoding="utf-8")

    # Write metadata
    (output_dir / "slide_metadata.json").write_text(
        json.dumps(slides_data, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    return {"slides": slides_data, "total_slides": len(slides_data), "md_path": str(output_dir / "extracted.md")}


def extract_from_docx(input_path: Path, output_dir: Path) -> dict:
    """Extract text from DOCX file."""
    # Use existing converter
    scripts_dir = Path(__file__).resolve().parent
    converter = scripts_dir / "source_to_md" / "doc_to_md.py"

    if converter.exists():
        import subprocess
        result = subprocess.run(
            [sys.executable, str(converter), str(input_path)],
            capture_output=True, text=True, cwd=str(scripts_dir.parent.parent)
        )
        if result.returncode == 0:
            # Find output md
            md_path = input_path.with_suffix(".md")
            if md_path.exists():
                md_content = md_path.read_text(encoding="utf-8")
            else:
                md_content = result.stdout
        else:
            md_content = f"Error converting: {result.stderr[:500]}"
    else:
        # Fallback: use python-docx
        try:
            from docx import Document
            doc = Document(str(input_path))
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            md_content = "\n\n".join(paragraphs)
        except Exception as e:
            md_content = f"Error: {e}"

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "extracted.md").write_text(md_content, encoding="utf-8")

    # Parse into slides (split by headers)
    slides_data = _parse_markdown_to_slides(md_content)
    (output_dir / "slide_metadata.json").write_text(
        json.dumps(slides_data, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    return {"slides": slides_data, "total_slides": len(slides_data), "md_path": str(output_dir / "extracted.md")}


def extract_from_pdf(input_path: Path, output_dir: Path) -> dict:
    """Extract text + images from PDF file."""
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(str(input_path))
    except ImportError:
        # Fallback to converter script
        return extract_from_docx(input_path, output_dir)

    images_dir = output_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    slides_data = []
    all_text = []

    for page_idx, page in enumerate(doc, 1):
        text = page.get_text("text").strip()

        # Extract images
        slide_images = []
        for img_idx, img in enumerate(page.get_images(full=True), 1):
            xref = img[0]
            base_image = doc.extract_image(xref)
            ext = base_image["ext"]
            img_name = f"slide_{page_idx:02d}_image_{img_idx:02d}.{ext}"
            img_path = images_dir / img_name
            with open(img_path, "wb") as f:
                f.write(base_image["image"])
            slide_images.append(img_name)

        title = text.split("\n")[0][:80] if text else f"Page {page_idx}"

        slides_data.append({
            "slide_number": page_idx,
            "title": title,
            "content_raw": text,
            "images_extracted": slide_images,
            "layout_hint": "content",
        })

        all_text.append(f"## Page {page_idx}: {title}\n\n{text}")

    doc.close()

    output_dir.mkdir(parents=True, exist_ok=True)
    md_content = "\n\n".join(all_text)
    (output_dir / "extracted.md").write_text(md_content, encoding="utf-8")
    (output_dir / "slide_metadata.json").write_text(
        json.dumps(slides_data, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    return {"slides": slides_data, "total_slides": len(slides_data), "md_path": str(output_dir / "extracted.md")}


def _parse_markdown_to_slides(md_content: str) -> list:
    """Parse markdown into slide objects by headers."""
    slides = []
    current_slide = None
    slide_num = 0

    for line in md_content.split("\n"):
        # Detect headers as slide boundaries
        if re.match(r"^#{1,3}\s+", line):
            if current_slide and current_slide["content_raw"].strip():
                slides.append(current_slide)
            slide_num += 1
            title = re.sub(r"^#{1,3}\s+", "", line).strip()
            current_slide = {
                "slide_number": slide_num,
                "title": title,
                "content_raw": "",
                "images_extracted": [],
                "layout_hint": "content",
            }
        elif current_slide:
            current_slide["content_raw"] += line + "\n"
        else:
            # Content before first header
            slide_num += 1
            current_slide = {
                "slide_number": slide_num,
                "title": "Introduction",
                "content_raw": line + "\n",
                "images_extracted": [],
                "layout_hint": "title_slide",
            }

    if current_slide and current_slide["content_raw"].strip():
        slides.append(current_slide)

    # If no slides found, treat entire content as 1 slide
    if not slides:
        slides = [{
            "slide_number": 1,
            "title": "Content",
            "content_raw": md_content,
            "images_extracted": [],
            "layout_hint": "content",
        }]

    return slides


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Extract slide assets from documents")
    parser.add_argument("input_file", help="Input file (PPTX/DOCX/PDF)")
    parser.add_argument("-o", "--output", default=None, help="Output directory")
    args = parser.parse_args()

    input_path = Path(args.input_file)
    if not input_path.exists():
        print(f"Error: File not found: {input_path}", file=sys.stderr)
        return 1

    output_dir = Path(args.output) if args.output else Path("sources")
    output_dir.mkdir(parents=True, exist_ok=True)

    suffix = input_path.suffix.lower()
    if suffix == ".pptx":
        result = extract_from_pptx(input_path, output_dir)
    elif suffix == ".pdf":
        result = extract_from_pdf(input_path, output_dir)
    elif suffix in (".docx", ".doc"):
        result = extract_from_docx(input_path, output_dir)
    else:
        print(f"Unsupported format: {suffix}", file=sys.stderr)
        return 1

    print(f"[OK] Extracted {result['total_slides']} slides")
    print(f"[OK] Markdown: {result['md_path']}")
    print(f"[OK] Metadata: {output_dir / 'slide_metadata.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
