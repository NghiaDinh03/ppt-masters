#!/usr/bin/env python3
"""
Vision Analyze Slides v2 — 3-step approach

Step 1: Trích xuất text bằng python-pptx (đã có trong extract_slide_assets.py)
Step 2: Hình nào không trích xuất được text -> push lên vision AI -> match vào markdown
Step 3: Gửi markdown hoàn chỉnh lên text AI để tổng hợp và diễn giải

System prompt tiếng Việt có dấu.

Usage:
    python3 vision_analyze_slides.py <project_path> [--llm openclaude|ollama]
"""

import sys
import os
import json
import base64
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

# Windows console encoding fix
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


# ─────────────────────────────────────────────────────────────
# System Prompts (Tiếng Việt có dấu)
# ─────────────────────────────────────────────────────────────

VISION_SYSTEM_PROMPT = """Bạn là chuyên gia phân tích tài liệu trình bày (presentation).
Nhiệm vụ: Phân tích hình ảnh slide và trích xuất TOÀN BỘ nội dung từ hình ảnh.

QUY TẮC BẮT BUỘC:
1. Đọc TẤT CẢ text trong hình ảnh (bao gồm số liệu, chữ, ký tự đặc biệt)
2. Nếu có bảng/biểu đồ → trích xuất dữ liệu chính xác (số, phần trăm, tên mục)
3. Nếu có sơ đồ/thiết kế → mô tả cấu trúc và các thành phần
4. Nếu có chart (biểu đồ) → trích xuất giá trị dữ liệu, trục X/Y, legend
5. Nếu có sơ đồ mạng/quy trình → mô tả từng bước, từng thành phần
6. Ghi nhận TẤT CẢ chi tiết — không được bỏ qua bất kỳ thông tin nào
7. Nếu hình ảnh mờ/blur → ghi nhận "không rõ" thay vì đoán

Output JSON format:
{
  "title": "Tiêu đề slide (từ hình ảnh)",
  "content": "Nội dung đầy đủ trích xuất từ hình ảnh",
  "data_points": ["Dữ liệu 1: giá trị", "Dữ liệu 2: giá trị"],
  "diagram_description": "Mô tả sơ đồ/biểu đồ nếu có",
  "table_data": ["hàng 1: cột1 | cột2 | cột3", "hàng 2: ..."],
  "key_insights": ["Insight 1", "Insight 2"],
  "image_type": "chart|diagram|screenshot|table|photo|mixed"
}"""


ENRICH_SYSTEM_PROMPT = """Bạn là chuyên gia thiết kế bài giảng và nội dung giáo dục.
Nhiệm vụ: Tổng hợp và DIỄN GIẢI chi tiết nội dung slide cho người học.

QUY TẮC BẮT BUỘC:
1. GIỮ LẠI TẤT CẢ thông tin quan trọng — KHÔNG được tóm tắt hay rút gọn
2. Bổ sung giải thích, ví dụ minh họa khi cần thiết
3. Sử dụng ngôn ngữ đơn giản, dễ tiếp cận cho người học
4. Format: bullet points rõ ràng, có tiêu đề phụ nếu cần
5. Nếu có dữ liệu số → giữ nguyên số, thêm context giải thích
6. Nếu có nội dung từ hình ảnh (OCR/vision) → ghép vào nội dung chính hợp lý
7. Mục tiêu: Người đọc slide này hiểu ngay nội dung mà không cần nghe giảng thêm

VÍ DỤ:
- Input: "Con gà trống biết gáy"
- Output SAI (tóm tắt): "Có con gà trống biết gáy"
- Output ĐÚNG (diễn giải): "Con gà trống là con gà có khả năng phát ra tiếng gáy. Chỉ con gà trống mới biết gáy, con gà mái không biết gáy. Tiếng gáy của gà trống thường vang vào buổi sáng sớm, báo hiệu một ngày mới bắt đầu."

Output JSON format:
{
  "title": "Tiêu đề slide",
  "content": "Nội dung đã diễn giải chi tiết...",
  "bullet_points": ["Điểm 1 chi tiết", "Điểm 2 chi tiết"],
  "summary": "Tóm tắt 1-2 câu",
  "image_hint": "mô tả hình ảnh minh họa phù hợp"
}"""


def vision_analyze_slides(project_path: Path, llm_provider: str = "openclaude") -> dict:
    """3-step analysis: extract -> vision -> text enrichment.

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

    print(f"[vision] Phân tích {len(slides)} slides với {llm_provider}...")

    # ── Step 2: Vision analysis cho slides có hình ──
    print(f"\n[vision] === STEP 2: Phân tích hình ảnh bằng Vision AI ===")
    vision_results = []
    vision_count = 0
    skip_count = 0

    for i, slide in enumerate(slides):
        num = slide.get("slide_number", 0)
        title = slide.get("title", "")
        content = slide.get("content_raw", "")
        slide_images = slide.get("images_extracted", [])
        text_length = slide.get("text_length", 0)

        # Quyết định: có cần vision AI không?
        # Nếu text đã đủ dài (>100 chars) và không có hình -> skip vision
        if not slide_images:
            vision_results.append({
                "slide_number": num, "title": title, "content": content,
                "data_points": [], "diagram_description": "",
                "table_data": slide.get("table_data", []),
                "key_insights": [], "image_type": "text_only", "has_image": False,
                "needs_vision": False,
            })
            skip_count += 1
            continue

        # Có hình -> kiểm tra xem text đã đủ chưa
        if text_length > 100 and not any(kw in title.lower() for kw in ["sla", "chart", "bieu do", "so do", "tong ket", "thong ke"]):
            # Text đã đủ, hình chỉ là minh họa -> không cần vision
            vision_results.append({
                "slide_number": num, "title": title, "content": content,
                "data_points": [], "diagram_description": "",
                "table_data": slide.get("table_data", []),
                "key_insights": [], "image_type": "illustration", "has_image": True,
                "needs_vision": False,
            })
            skip_count += 1
            print(f"[vision] Slide {num}: {title[:40]}... -> text đủ, skip vision")
            continue

        # Cần vision AI -> gửi hình lên
        print(f"[vision] Slide {num}: {title[:40]}... -> gửi {len(slide_images)} hình lên vision AI")

        img_paths = []
        for img_name in slide_images:
            img_path = images_dir / img_name
            if img_path.exists():
                img_paths.append(str(img_path))

        if not img_paths:
            vision_results.append({
                "slide_number": num, "title": title, "content": content,
                "data_points": [], "diagram_description": "",
                "table_data": slide.get("table_data", []),
                "key_insights": [], "image_type": "no_images", "has_image": False,
                "needs_vision": False,
            })
            continue

        try:
            vision_result = _analyze_with_vision(img_paths, title, content, llm_provider)
            vision_result["slide_number"] = num
            vision_result["has_image"] = True
            vision_result["needs_vision"] = True
            vision_results.append(vision_result)
            vision_count += 1
            print(f"[vision]   OK - {vision_result.get('image_type', 'unknown')}")
        except Exception as e:
            print(f"[vision]   ERROR: {str(e)[:80]}")
            vision_results.append({
                "slide_number": num, "title": title, "content": content,
                "data_points": [], "diagram_description": "",
                "table_data": slide.get("table_data", []),
                "key_insights": [], "image_type": "error", "has_image": True,
                "needs_vision": True, "error": str(e)[:200],
            })

    # Save vision results
    vision_path = project_path / "vision_analysis.json"
    vision_path.write_text(json.dumps(vision_results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[vision] Step 2 hoàn thành: {vision_count} slides phân tích bằng vision, {skip_count} skip")

    # ── Step 3: Text enrichment cho TẤT CẢ slides ──
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
            content_md += f"\n\n**Tóm tắt:** {slide['summary']}"
        (slide_dir / "content.md").write_text(content_md, encoding="utf-8")

    success_count = sum(1 for s in enriched_slides if s.get("enriched"))
    print(f"\n[vision] Step 3 hoàn thành: {success_count}/{len(enriched_slides)} slides được diễn giải")
    print(f"[vision] Đã lưu: {enriched_path}")

    return {
        "total_slides": len(enriched_slides),
        "vision_count": vision_count,
        "enriched_count": success_count,
    }


def _analyze_with_vision(img_paths: list, title: str, content: str, provider: str) -> dict:
    """Send images to vision AI for analysis."""
    if provider == "openclaude":
        return _vision_openclaude(img_paths, title, content)
    elif provider == "ollama":
        return _vision_ollama(img_paths, title, content)
    else:
        return _vision_openclaude(img_paths, title, content)


def _vision_openclaude(img_paths: list, title: str, content: str) -> dict:
    """Use Open Claude with vision model."""
    try:
        from openai import OpenAI
    except ImportError:
        raise ImportError("openai package required. pip install openai")

    try:
        from config import load_prefixed_env_file
        load_prefixed_env_file(("LLM_",))
    except Exception:
        pass

    api_key = os.environ.get("LLM_API_KEY", "")
    base_url = os.environ.get("LLM_BASE_URL", "https://open-claude.com/v1")
    model = os.environ.get("LLM_VISION_MODEL", os.environ.get("LLM_MODEL", "kimi-k2.5"))

    if not api_key:
        raise ValueError("LLM_API_KEY not set")

    client = OpenAI(api_key=api_key, base_url=base_url)

    # Build message with images
    content_parts = [
        {"type": "text", "text": f"Phân tích hình ảnh slide sau và trích xuất TOÀN BỘ nội dung.\n\nTiêu đề: {title}\nNội dung text đã trích xuất: {content[:1000]}"}
    ]

    for img_path in img_paths[:3]:
        try:
            with open(img_path, "rb") as f:
                img_data = base64.b64encode(f.read()).decode("utf-8")
            ext = Path(img_path).suffix.lower()
            mime = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "webp": "image/webp"}.get(ext.lstrip("."), "image/jpeg")
            content_parts.append({
                "type": "image_url",
                "image_url": {"url": f"data:{mime};base64,{img_data}"}
            })
        except Exception as e:
            print(f"[vision]   Không thể load hình {img_path}: {e}")

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": VISION_SYSTEM_PROMPT},
            {"role": "user", "content": content_parts},
        ],
        max_tokens=2000,
        temperature=0.3,
    )

    result_text = response.choices[0].message.content
    return _parse_json_response(result_text, title, content)


def _vision_ollama(img_paths: list, title: str, content: str) -> dict:
    """Use Ollama with vision model."""
    import requests

    endpoint = os.environ.get("OLLAMA_ENDPOINT", "http://localhost:11434")
    model = os.environ.get("OLLAMA_VISION_MODEL", "llava:13b")

    images_b64 = []
    for img_path in img_paths[:3]:
        try:
            with open(img_path, "rb") as f:
                images_b64.append(base64.b64encode(f.read()).decode("utf-8"))
        except Exception:
            pass

    prompt = f"{VISION_SYSTEM_PROMPT}\n\nPhân tích hình ảnh slide sau:\nTiêu đề: {title}\nNội dung: {content[:1000]}"

    resp = requests.post(
        f"{endpoint}/api/generate",
        json={"model": model, "prompt": prompt, "images": images_b64, "stream": False},
        timeout=120,
    )
    resp.raise_for_status()
    result_text = resp.json().get("response", "")
    return _parse_json_response(result_text, title, content)


def _enrich_all_slides(vision_results: list, provider: str) -> list:
    """Step 3: Enrich ALL slides with text AI."""
    enriched = []

    for vr in vision_results:
        num = vr.get("slide_number", 0)
        title = vr.get("title", "")
        content = vr.get("content", "")

        # Merge vision data vào content
        if vr.get("data_points"):
            content += "\n\nDữ liệu:\n" + "\n".join(f"- {dp}" for dp in vr["data_points"])
        if vr.get("diagram_description"):
            content += f"\n\nMô tả sơ đồ: {vr['diagram_description']}"
        if vr.get("table_data"):
            content += "\n\nBảng dữ liệu:\n" + "\n".join(vr["table_data"])
        if vr.get("key_insights"):
            content += "\n\nNhận định:\n" + "\n".join(f"- {ki}" for ki in vr["key_insights"])

        # Thử AI enrichment
        try:
            result = _enrich_with_ai(title, content, provider)
            result["slide_number"] = num
            result["type"] = vr.get("image_type", "content")
            result["enriched"] = True
            enriched.append(result)
            print(f"[enrich] Slide {num}: OK")
        except Exception as e:
            print(f"[enrich] Slide {num}: Thất bại ({str(e)[:60]})")
            enriched.append({
                "slide_number": num, "type": vr.get("image_type", "content"),
                "title": title, "content": content,
                "bullet_points": [], "summary": "", "enriched": False,
                "image_hint": f"hình ảnh liên quan đến {title}",
            })

    return enriched


def _enrich_with_ai(title: str, content: str, provider: str) -> dict:
    """Enrich a single slide with text AI."""
    if provider == "openclaude":
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
        model = os.environ.get("LLM_MODEL", "kimi-k2.5")

        client = OpenAI(api_key=api_key, base_url=base_url)

        prompt = f"Tiêu đề: {title}\nNội dung:\n{content[:3000]}\n\nHãy diễn giải chi tiết và trả về JSON."

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

    elif provider == "ollama":
        import requests
        endpoint = os.environ.get("OLLAMA_ENDPOINT", "http://localhost:11434")
        model = os.environ.get("OLLAMA_MODEL", "gemma4:8b")

        prompt = f"{ENRICH_SYSTEM_PROMPT}\n\nTiêu đề: {title}\nNội dung:\n{content[:3000]}"

        resp = requests.post(
            f"{endpoint}/api/generate",
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=120,
        )
        resp.raise_for_status()
        result_text = resp.json().get("response", "")
        return _parse_json_response(result_text, title, content)

    else:
        raise ValueError(f"Unknown provider: {provider}")


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
        import re
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
            "image_hint": f"hình ảnh liên quan đến {fallback_title}",
        }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Vision analyze slides (3-step approach)")
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
