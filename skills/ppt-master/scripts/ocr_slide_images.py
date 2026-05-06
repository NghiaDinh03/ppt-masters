#!/usr/bin/env python3
"""
OCR Slide Images — Trích xuất text từ hình ảnh trong slide

Sử dụng Tesseract OCR (miễn phí) hoặc EasyOCR để đọc text từ hình ảnh.
Sau đó gộp text extracted vào nội dung slide.

Usage:
    python3 ocr_slide_images.py <project_path> [--engine tesseract|easyocr]
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


def ocr_slide_images(project_path: Path, engine: str = "tesseract") -> dict:
    """Run OCR on all extracted images and merge text into slide content.

    Args:
        project_path: Project directory with sources/images/ and sources/slide_metadata.json
        engine: OCR engine ("tesseract" or "easyocr")

    Returns:
        Updated metadata dict.
    """
    metadata_path = project_path / "sources" / "slide_metadata.json"
    if not metadata_path.exists():
        print("[ocr] No slide_metadata.json found, skipping OCR")
        return {}

    slides = json.loads(metadata_path.read_text(encoding="utf-8"))
    images_dir = project_path / "sources" / "images"

    if not images_dir.exists():
        print("[ocr] No images directory found, skipping OCR")
        return {"slides": slides, "ocr_count": 0}

    # Initialize OCR engine
    ocr_func = None
    if engine == "easyocr":
        ocr_func = _init_easyocr()
    if ocr_func is None:
        ocr_func = _init_tesseract()
    if ocr_func is None:
        print("[ocr] WARNING: No OCR engine available. Install pytesseract or easyocr.")
        print("[ocr]   pip install pytesseract  (requires Tesseract binary)")
        print("[ocr]   pip install easyocr")
        return {"slides": slides, "ocr_count": 0}

    ocr_count = 0
    total_chars = 0

    for slide in slides:
        slide_images = slide.get("images_extracted", [])
        if not slide_images:
            continue

        slide_num = slide.get("slide_number", 0)
        ocr_texts = []

        for img_name in slide_images:
            img_path = images_dir / img_name
            if not img_path.exists():
                continue

            print(f"[ocr] Slide {slide_num}: {img_name}...", end=" ")
            try:
                text = ocr_func(str(img_path))
                if text and len(text.strip()) > 5:
                    ocr_texts.append(text.strip())
                    ocr_count += 1
                    total_chars += len(text.strip())
                    print(f"OK ({len(text)} chars)")
                else:
                    print("no text found")
            except Exception as e:
                print(f"error: {str(e)[:60]}")

        # Merge OCR text into slide content
        if ocr_texts:
            ocr_combined = "\n".join(ocr_texts)
            existing_content = slide.get("content_raw", "")

            # Add OCR text as additional content
            slide["ocr_text"] = ocr_combined
            slide["content_raw"] = existing_content + "\n\n[Noi dung tu hinh anh]\n" + ocr_combined

            # Update bullet points with OCR data
            for line in ocr_combined.split("\n"):
                line = line.strip()
                if line and len(line) > 3:
                    if line not in slide.get("bullet_points", []):
                        slide.setdefault("bullet_points", []).append(line)

    # Save updated metadata
    metadata_path.write_text(json.dumps(slides, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n[ocr] Complete: {ocr_count} images processed, {total_chars} chars extracted")
    return {"slides": slides, "ocr_count": ocr_count}


def _init_tesseract():
    """Initialize Tesseract OCR."""
    try:
        import pytesseract
        from PIL import Image

        # Check if tesseract binary is available
        try:
            pytesseract.get_tesseract_version()
        except Exception:
            # Try common Windows installation paths
            common_paths = [
                r"C:\Program Files\Tesseract-OCR\tesseract.exe",
                r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
                os.path.expanduser(r"~\AppData\Local\Tesseract-OCR\tesseract.exe"),
            ]
            for path in common_paths:
                if os.path.exists(path):
                    pytesseract.pytesseract.tesseract_cmd = path
                    break
            else:
                return None

        def ocr_tesseract(image_path: str) -> str:
            img = Image.open(image_path)
            # Try Vietnamese + English
            try:
                text = pytesseract.image_to_string(img, lang="vie+eng")
            except Exception:
                # Fallback to English only
                text = pytesseract.image_to_string(img, lang="eng")
            return text

        # Test
        print("[ocr] Using Tesseract OCR")
        return ocr_tesseract

    except ImportError:
        return None


def _init_easyocr():
    """Initialize EasyOCR."""
    try:
        import easyocr
        reader = easyocr.Reader(["vi", "en"], gpu=False)

        def ocr_easyocr(image_path: str) -> str:
            results = reader.readtext(image_path)
            texts = [r[1] for r in results if r[2] > 0.3]  # confidence > 0.3
            return "\n".join(texts)

        print("[ocr] Using EasyOCR")
        return ocr_easyocr

    except ImportError:
        return None


def main():
    import argparse
    parser = argparse.ArgumentParser(description="OCR slide images")
    parser.add_argument("project_path", help="Project directory")
    parser.add_argument("--engine", default="tesseract", choices=["tesseract", "easyocr"],
                        help="OCR engine (default: tesseract)")
    args = parser.parse_args()

    project_path = Path(args.project_path)
    if not project_path.exists():
        print(f"Error: Directory not found: {project_path}", file=sys.stderr)
        return 1

    ocr_slide_images(project_path, args.engine)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
