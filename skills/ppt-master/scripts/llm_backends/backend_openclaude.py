#!/usr/bin/env python3
"""
Open Claude LLM Backend (OpenAI-compatible API)

Uses Open Claude gateway for LLM operations (content enrichment, summarization).
Supports kimi-k2.5 model for cost-efficient content processing.

Configuration (.env):
    LLM_API_KEY     (required) Open Claude API key
    LLM_BASE_URL    (optional) API endpoint (default: https://open-claude.com/v1)
    LLM_MODEL       (optional) Model name (default: kimi-k2.5)

Usage:
    from llm_backends.backend_openclaude import chat_completion, enrich_slide_content
"""

import os
import sys
import json


# Windows console encoding fix
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

_SCRIPTS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False


def _load_config():
    """Load LLM config from environment."""
    try:
        from config import load_prefixed_env_file
        load_prefixed_env_file(("LLM_",))
    except Exception:
        pass

    return {
        "api_key": os.environ.get("LLM_API_KEY", ""),
        "base_url": os.environ.get("LLM_BASE_URL", "https://open-claude.com/v1"),
        "model": os.environ.get("LLM_MODEL", "kimi-k2.5"),
    }


def chat_completion(prompt: str, system_prompt: str = None, max_tokens: int = 4000, temperature: float = 0.7) -> str:
    """Send a chat completion request to Open Claude."""
    config = _load_config()

    if not config["api_key"]:
        raise ValueError("LLM_API_KEY not set. Add it to .env file.")

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    if HAS_OPENAI:
        client = OpenAI(api_key=config["api_key"], base_url=config["base_url"])
        response = client.chat.completions.create(
            model=config["model"], messages=messages,
            max_tokens=max_tokens, temperature=temperature,
        )
        return response.choices[0].message.content

    if HAS_HTTPX:
        headers = {"Authorization": f"Bearer {config['api_key']}", "Content-Type": "application/json"}
        body = {"model": config["model"], "messages": messages, "max_tokens": max_tokens, "temperature": temperature}
        with httpx.Client(timeout=120.0) as client:
            resp = client.post(f"{config['base_url']}/chat/completions", headers=headers, json=body)
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]

    import requests
    headers = {"Authorization": f"Bearer {config['api_key']}", "Content-Type": "application/json"}
    body = {"model": config["model"], "messages": messages, "max_tokens": max_tokens, "temperature": temperature}
    resp = requests.post(f"{config['base_url']}/chat/completions", headers=headers, json=body, timeout=120)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


ENRICH_SYSTEM_PROMPT = """Bạn là chuyên gia thiết kế bài giảng và nội dung giáo dục.
Nhiệm vụ: DIỄN GIẢI chi tiết và dễ hiểu nội dung slide cho người học.

QUY TẮC BẮT BUỘC:
1. GIỮ LẠI TẤT CẢ thông tin quan trọng — KHÔNG được tóm tắt hay rút gọn
2. Bổ sung giải thích, ví dụ minh họa khi cần thiết
3. Sử dụng ngôn ngữ đơn giản, dễ tiếp cận cho người học
4. Format: bullet points rõ ràng, có tiêu đề phụ nếu cần
5. Nếu có dữ liệu số -> giữ nguyên số, thêm context giải thích
6. Mục tiêu: Người đọc slide này hiểu ngay nội dung mà không cần nghe giảng thêm

VÍ DỤ:
- Input: "Con gà trống biết gáy"
- Output SAI (tóm tắt): "Có con gà trống biết gáy"
- Output ĐÚNG (diễn giải): "Con gà trống là con gà có khả năng phát ra tiếng gáy. Chỉ con gà trống mới biết gáy, con gà mái không biết gáy. Tiếng gáy của gà trống thường vang vào buổi sáng sớm, báo hiệu một ngày mới bắt đầu."

Output JSON format:
{
  "title": "Tiêu đề slide",
  "content": "Nội dung đã diễn giải chi tiết...",
  "bullet_points": ["Điểm 1 chi tiết", "Điểm 2 chi tiết"],
  "image_hint": "mô tả hình ảnh minh họa phù hợp"
}"""


def enrich_slide_content(slide_data: dict) -> dict:
    """Enrich a single slide's content with detailed explanation."""
    title = slide_data.get("title", "")
    content = slide_data.get("content_raw", slide_data.get("content", ""))
    slide_type = slide_data.get("type", "content")

    if not content.strip():
        return {**slide_data, "content": content, "bullet_points": [], "enriched": False, "image_hint": ""}

    prompt = f"""Hãy diễn giải chi tiết nội dung slide sau:

Tiêu đề: {title}
Loại slide: {slide_type}
Nội dung gốc:
{content[:3000]}

Hãy trả về JSON với nội dung đã diễn giải chi tiết, dễ hiểu cho người học."""

    try:
        response = chat_completion(prompt, system_prompt=ENRICH_SYSTEM_PROMPT, max_tokens=2000, temperature=0.7)
        clean = response.strip()
        if clean.startswith("```"):
            clean = clean.split("\n", 1)[1] if "\n" in clean else clean[3:]
            if clean.endswith("```"):
                clean = clean[:-3]
            clean = clean.strip()

        enriched = json.loads(clean)
        enriched["enriched"] = True
        enriched["slide_number"] = slide_data.get("slide_number", 0)
        enriched["type"] = slide_type
        return enriched
    except (json.JSONDecodeError, Exception) as e:
        print(f"[openclaude] Enrich failed for slide {slide_data.get('slide_number', '?')}: {e}")
        return {
            "slide_number": slide_data.get("slide_number", 0), "type": slide_type,
            "title": title, "content": content, "bullet_points": [],
            "enriched": False, "image_hint": f"hình ảnh liên quan đến {title}",
        }


def generate_image_prompt(slide_data: dict) -> str:
    """Generate an image search/generation prompt from slide content."""
    title = slide_data.get("title", "")
    content = slide_data.get("content", "")[:500]
    prompt = f"""Từ nội dung slide sau, hãy tạo 1 câu mô tả hình ảnh ngắn gọn (dưới 20 từ)
để tìm kiếm hoặc tạo hình ảnh minh họa phù hợp. Chỉ trả về câu mô tả, không giải thích.

Tiêu đề: {title}
Nội dung: {content}"""
    try:
        response = chat_completion(prompt, max_tokens=100, temperature=0.5)
        return response.strip().strip('"').strip("'")
    except Exception:
        return f"hình ảnh liên quan đến {title}"


if __name__ == "__main__":
    config = _load_config()
    print(f"Config: base_url={config['base_url']}, model={config['model']}")
    print(f"API key: {'SET' if config['api_key'] else 'NOT SET'}")
    if config["api_key"]:
        try:
            result = chat_completion("Trả lời bằng 1 từ: OK")
            print(f"Test response: {result}")
        except Exception as e:
            print(f"Test failed: {e}")
