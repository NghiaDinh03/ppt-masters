#!/usr/bin/env python3
"""
Vision Analyze Slides v3 — OCR-based approach

Step 1: python-pptx trích text từ PPTX (text frame, table, group, chart)
Step 2: OCR trích text từ HÌNH (chart, diagram, screenshot) -> gộp vào markdown
Step 3: Gửi markdown hoàn chỉnh lên text AI -> phân tích, tóm tắt

Không cần vision multimodal AI — chỉ cần OCR + text AI.
Không bị content filter chặn vì chỉ gửi text, không gửi hình.

Usage:
    python3 vision_analyze_slides.py <project_path> [--llm openclaude|ollama]
"""

import sys
import os
import json
import re
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


ENRICH_SYSTEM_PROMPT = """Bạn là chuyên gia thiết kế bài giảng và nội dung giáo dục.
Nhiệm vụ: Tổng hợp và DIỄN GIẢI chi tiết nội dung slide cho người học.

QUY TẮC BẮT BUỘC:
1. GIỮ LẠI TẤT CẢ thông tin quan trọng — KHÔNG được tóm tắt hay rút gọn
2. Bổ sung giải thích, ví dụ minh họa khi cần thiết
3. Sử dụng ngôn ngữ đơn giản, dễ tiếp cận cho người học
4. Format: bullet points rõ ràng, có tiêu đề phụ nếu cần
5. Nếu có dữ liệu số → giữ nguyên số, thêm context giải thích
6. Nếu có nội dung từ OCR (hình ảnh) → ghép vào nội dung chính hợp lý
7. Mục tiêu: Người đọc slide này hiểu ngay nội dung mà không cần nghe giảng thêm

Output JSON format:
{
  "title": "Tiêu đề slide",
  "content": "Nội dung đã diễn giải chi tiết...",
  "bullet_points": ["Điểm 1 chi tiết", "Điểm 2 chi tiết"],
  "summary": "Tóm tắt 1-2 câu",
  "image_hint": "mô tả hình ảnh minh họa phù hợp"
}"""


def _init_ocr():
    """Initialize OCR engine (EasyOCR preferred, Tesseract fallback)."""
    # Try EasyOCR
    try:
        import easyocr
        reader = easyocr.Reader(["vi", "en"], gpu=False)
        def ocr_easyocr(image_path):
            results = reader.readtext(image_path)
            texts = [r[1] for r in results if r[2] > 0.3]
            return "\n".join(texts)
        print("[ocr] Using EasyOCR (vi+en)")
        return ocr_easyocr
    except ImportError:
        pass

    # Try Tesseract
    try:
        import pytesseract
        from PIL import Image
        try:
            pytesseract.get_tesseract_version()
        except Exception:
            common_paths = [
                r"C:\Program Files\Tesseract-OCR\tesseract.exe",
                r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
                os.path.expanduser(r"~\AppData\Local\Tesseract-OCR\tesseract.exe"),
            ]
            for p in common_paths:
                if os.path.exists(p):
                    pytesseract.pytesseract.tesseract_cmd = p
                    break
            else:
                return None

        def ocr_tesseract(image_path):
            img = Image.open(image_path)
            try:
                return pytesseract.image_to_string(img, lang="vie+eng")
            except Exception:
                return pytesseract.image_to_string(img, lang="eng")
        print("[ocr] Using Tesseract")
        return ocr_tesseract
    except ImportError:
        pass

    return None


def vision_analyze_slides(project_path: Path, llm_provider: str = "openclaude") -> dict:
    """3-step analysis: extract -> OCR images -> text enrichment.

    Args:
        project_path: Project directory
        llm_provider: LLM provider

    Returns:
        Analysis results.
    """
    metadata_path = project_path / "sources" / "slide_metadata.json"
    if not metadata_path.exists():
        raise FileNotFoundError(f"slide_metadata.json not found")

    slides = json.loads(metadata_path.read_text(encoding="utf-8"))
    images_dir = project_path / "sources" / "images"

    print(f"[vision] Phân tích {len(slides)} slides...")

    # ── Step 2: OCR images + merge vào content ──
    print(f"\n[vision] === STEP 2: OCR hình ảnh + gộp vào content ===")
    ocr_func = _init_ocr()
    ocr_count = 0
    vision_results = []

    for i, slide in enumerate(slides):
        num = slide.get("slide_number", 0)
        title = slide.get("title", "")
        content = slide.get("content_raw", "")
        slide_images = slide.get("images_extracted", [])

        ocr_text = ""
        if slide_images and ocr_func:
            for img_name in slide_images:
                img_path = images_dir / img_name
                if img_path.exists():
                    try:
                        text = ocr_func(str(img_path))
                        if text and len(text.strip()) > 5:
                            ocr_text += text.strip() + "\n"
                            ocr_count += 1
                            print(f"[ocr]   Slide {num}: {img_name} -> {len(text)} chars")
                    except Exception as e:
                        print(f"[ocr]   Slide {num}: {img_name} -> error: {str(e)[:60]}")
        elif slide_images and not ocr_func:
            print(f"[ocr]   Slide {num}: có {len(slide_images)} hình nhưng chưa cài OCR engine")

        # Merge OCR text vào content
        full_content = content
        if ocr_text:
            full_content = content + "\n\n[Noi dung tu hinh anh]\n" + ocr_text

        vision_results.append({
            "slide_number": num, "title": title, "content": full_content,
            "ocr_text": ocr_text.strip(),
            "data_points": [], "diagram_description": "",
            "table_data": slide.get("table_data", []),
            "key_insights": [], "image_type": "ocr" if ocr_text else "text_only",
            "has_image": bool(slide_images),
        })

    # Save vision results
    vision_path = project_path / "vision_analysis.json"
    vision_path.write_text(json.dumps(vision_results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[vision] Step 2 hoàn thành: {ocr_count} hình OCR thành công")

    # ── Step 3: Text enrichment ──
    print(f"\n[vision] === STEP 3: Tổng hợp nội dung bằng Text AI ===")
    enriched_slides = _enrich_all_slides(vision_results, llm_provider)

    # Save enriched results
    enriched_path = project_path / "slides_enriched.json"
    enriched_path.write_text(json.dumps(enriched_slides, ensure_ascii=False, indent=2), encoding="utf-8")

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
        if slide.get("summary"):
            content_md += f"\n\n**Tom tat:** {slide['summary']}"
        (slide_dir / "content.md").write_text(content_md, encoding="utf-8")

    success_count = sum(1 for s in enriched_slides if s.get("enriched"))
    print(f"\n[vision] Step 3 hoan thanh: {success_count}/{len(enriched_slides)} slides duoc dien giai")
    print(f"[vision] Da luu: {enriched_path}")

    return {
        "total_slides": len(enriched_slides),
        "ocr_count": ocr_count,
        "enriched_count": success_count,
    }


def _enrich_all_slides(vision_results: list, provider: str) -> list:
    """Step 3: Enrich ALL slides with text AI."""
    enriched = []

    for vr in vision_results:
        num = vr.get("slide_number", 0)
        title = vr.get("title", "")
        content = vr.get("content", "")

        try:
            result = _enrich_with_ai(title, content, provider)
            result["slide_number"] = num
            result["type"] = vr.get("image_type", "content")
            result["enriched"] = True
            enriched.append(result)
            print(f"[enrich] Slide {num}: OK")
        except Exception as e:
            print(f"[enrich] Slide {num}: That bai ({str(e)[:60]})")
            enriched.append({
                "slide_number": num, "type": vr.get("image_type", "content"),
                "title": title, "content": content,
                "bullet_points": [], "summary": "", "enriched": False,
                "image_hint": f"hinh anh lien quan den {title}",
            })

    return enriched


def _enrich_with_ai(title: str, content: str, provider: str) -> dict:
    """Enrich a single slide with text AI. Fallback chain: cloud -> ollama."""
    if provider == "ollama":
        return _enrich_ollama(title, content)

    # Try cloud first
    try:
        return _enrich_cloud(title, content)
    except Exception as e:
        error_msg = str(e).lower()
        if "blocked" in error_msg or "stream ended" in error_msg or "timeout" in error_msg or "connection" in error_msg:
            print(f"[enrich]   Cloud failed, falling back to Ollama...")
            try:
                return _enrich_ollama(title, content)
            except Exception as e2:
                print(f"[enrich]   Ollama also failed: {str(e2)[:60]}")
                raise e
        raise


def _enrich_cloud(title: str, content: str) -> dict:
    """Enrich using cloud API (Open Claude / DeepSeek)."""
    try:
        from openai import OpenAI
    except ImportError:
        raise ImportError("openai package required")

    try:
        from config import load_prefixed_env_file
        load_prefixed_env_file(("LLM_",))
    except Exception:
        pass

    api_key = os.environ.get("LLM_API_KEY", "")
    base_url = os.environ.get("LLM_BASE_URL", "https://open-claude.com/v1")
    model = os.environ.get("LLM_MODEL", "deepseek-v4-flash")

    if not api_key:
        raise ValueError("LLM_API_KEY not set")

    client = OpenAI(api_key=api_key, base_url=base_url)
    prompt = f"Tieu de: {title}\nNoi dung:\n{content[:3000]}\n\nHay dien giai chi tiet va tra ve JSON."

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": ENRICH_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        max_tokens=2000,
        temperature=0.7,
    )

    result_text = response.choices[0].message.content
    return _parse_json_response(result_text, title, content)


def _enrich_ollama(title: str, content: str) -> dict:
    """Enrich using Ollama local model."""
    import requests
    endpoint = os.environ.get("OLLAMA_ENDPOINT", "http://localhost:11434")
    model = os.environ.get("OLLAMA_MODEL", "gemma3:4b")

    prompt = f"{ENRICH_SYSTEM_PROMPT}\n\nTieu de: {title}\nNoi dung:\n{content[:3000]}"

    resp = requests.post(
        f"{endpoint}/api/generate",
        json={"model": model, "prompt": prompt, "stream": False},
        timeout=120,
    )
    resp.raise_for_status()
    result_text = resp.json().get("response", "")
    return _parse_json_response(result_text, title, content)


def _parse_json_response(text: str, fallback_title: str, fallback_content: str) -> dict:
    """Parse JSON from AI response with fallback."""
    clean = text.strip()

    if clean.startswith("```"):
        lines = clean.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        clean = "\n".join(lines).strip()

    try:
        return json.loads(clean)
    except json.JSONDecodeError:
        json_match = re.search(r'\{[^{}]*\}', clean, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

        return {
            "title": fallback_title,
            "content": fallback_content,
            "bullet_points": [],
            "summary": "",
            "image_hint": f"hinh anh lien quan den {fallback_title}",
        }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Vision analyze slides (OCR + text AI)")
    parser.add_argument("project_path", help="Project directory")
    parser.add_argument("--llm", default="openclaude", choices=["openclaude", "ollama"],
                        help="LLM provider (default: openclaude)")
    args = parser.parse_args()

    project_path = Path(args.project_path)
    if not project_path.exists():
        print(f"Error: Directory not found: {project_path}", file=sys.stderr)
        return 1

    vision_analyze_slides(project_path, args.llm)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
