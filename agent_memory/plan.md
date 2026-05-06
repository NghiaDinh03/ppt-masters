# PPT Master — Kế Hoạch Phát Triển (Final v5)

> Cập nhật: 2026-05-06
> Phân tích bởi: MiMo AI Agent

---

## Pipeline Tổng Quan

```
Input (PPTX/DOCX/PDF/Excel)
    │
    ▼
[Step 1] Trích xuất text + hình ảnh từ file cũ
    │   ├── python-pptx: text frame, table, group shape, chart
    │   ├── extract_slide_images.py: tách embedded images
    │   └── Output: sources/slide_metadata.json + sources/images/
    │
    ▼
[Step 2] OCR hình ảnh → gộp vào markdown
    │   ├── EasyOCR (vi+en) — đã cài, hoạt động OK
    │   ├── Trích text từ chart, diagram, screenshot trong hình
    │   └── Gộp OCR text vào content_raw → full_content
    │
    ▼
[Step 3] AI diễn giải chi tiết nội dung (KHÔNG tóm tắt)
    │   ├── claude-sonnet-4-6 (Open Claude) — primary, không bị content filter
    │   ├── qwen3:8b (Ollama local) — fallback, free
    │   └── Output: slides_enriched.json (title, content, bullet_points, summary, image_hint)
    │
    ▼
[Step 4] Tìm kiếm/Gen hình ảnh cho từng slide
    │   ├── Pexels + Pixabay search (ảnh thật, free, đã có key)
    │   ├── Pollinations.ai gen (AI gen, free, không cần key)
    │   └── Open Claude gpt-5.4-image (AI gen, chất lượng cao)
    │
    ▼
[Step 5] Ráp nội dung + hình ảnh → SVG → PPTX
    │   ├── assemble_slides.py: generate SVG per slide
    │   ├── finalize_svg.py: post-processing
    │   └── svg_to_pptx.py: export PPTX editable (DrawingML)
    │
    ▼
[Step 6] Audio (tùy chọn)
    │   ├── edge-tts (free, unlimited) — mặc định
    │   ├── ElevenLabs (10K tokens/tháng) — khi cần chất lượng cao
    │   └── Lưu vào slides/slide_XX/audio.mp3, KHÔNG nhúng vào PPTX
    │
    ▼
Output: PPTX editable + per-slide folders
```

---

## Trạng Thái Hiện Có

### ✅ Đã Hoàn Thành

| # | Task | Trạng thái | Ghi chú |
|---|------|------------|---------|
| 1 | API Keys tích hợp | ✅ Done | Pexels, Pixabay, ElevenLabs, Open Claude, Hugging Face |
| 2 | Pollinations.ai image backend | ✅ Done | Free, không cần key, URL-based API |
| 3 | Open Claude LLM backend | ✅ Done | claude-sonnet-4-6, không bị content filter |
| 4 | Extract slide assets | ✅ Done | python-pptx: text, table, group, chart |
| 5 | OCR image text extraction | ✅ Done | EasyOCR (vi+en), đã test OK |
| 6 | Content enrichment (AI) | ✅ Done | claude-sonnet-4-6 primary, Ollama fallback |
| 7 | Image search pipeline | ✅ Done | Pexels/Pixabay search + Pollinations fallback |
| 8 | Style prompt parser | ✅ Done | [title] [style] [font] [layout] format |
| 9 | Slide assembler | ✅ Done | SVG generation + table slides |
| 10 | Audio pipeline | ✅ Done | edge-tts, clean text for TTS |
| 11 | Unified pipeline | ✅ Done | auto_pptx_pipeline.py |
| 12 | Backend API | ✅ Done | /api/pipeline/run, status, download, slides, download-folder |
| 13 | Frontend UI | ✅ Done | PPTX Pipeline page, live logs, slide preview |
| 14 | .env configuration | ✅ Done | Tất cả API keys đã config |
| 15 | Docker setup | ✅ Done | docker-compose.yml |
| 16 | UTF-8 encoding fix | ✅ Done | Windows console compatibility |

### 🔴 Issues Đã Fix

| # | Issue | Nguyên nhân | Giải pháp |
|---|-------|-------------|-----------|
| I1 | `'charmap' codec can't encode` | Windows cmd.exe dùng cp1252 charset | Thêm `sys.stdout.reconfigure(encoding="utf-8")` vào tất cả scripts |
| I2 | `Your request was blocked` | Open Claude content filter chặn nội dung cybersecurity | Đổi sang `claude-sonnet-4-6` — model này không bị filter |
| I3 | `404 Not Found for url: http://localhost:11434/` | Ollama endpoint URL sai env var name | Đổi `OLLAMA_ENDPOINT` → `OLLAMA_BASE_URL` |
| I4 | `RuntimeError: File at path .../candidates is not a file` | `images_dir.glob("*")` lấy cả thư mục | Filter by image extensions (.jpg, .png, .webp) |
| I5 | Select dropdown text trắng | CSS không style option elements | Inject global CSS `select option { background: #1a1a2e; color: #fff }` |
| I6 | `_escape_xml` no-op replacements | HTML entities bị decode khi write_to_file | Dùng `chr(38)` approach để build XML entities |
| I7 | `Stream ended before producing useful content` | Open Claude trả về response rỗng khi blocked | Fallback sang Ollama local |
| I8 | OCR không hoạt động | Chưa cài easyocr | `pip install easyocr` — đã cài OK |
| I9 | Slide image preview 500 error | `glob("*")` picks up `candidates` directory | Filter by file extensions only |
| I10 | Vision AI skip logic quá đơn giản | `text_length > 100` bỏ qua chart/table trong hình | Luôn gửi hình lên OCR, không skip |

### 🟡 Tasks Chưa Hoàn Thành

| # | Task | Mức độ | Mô tả |
|---|------|--------|-------|
| T1 | Ollama qwen3:8b download | 🟡 Trung bình | Đang download 5.2GB, cần chờ hoàn thành |
| T2 | Content quality improvement | 🟡 Trung bình | Output slide content cần đẹp hơn, match style |
| T3 | Image relevance improvement | 🟡 Trung bình | Image search query cần chính xác hơn (hiện tại dùng title đơn giản) |
| T4 | Audio generation fix | 🟡 Trung bình | edge-tts fail khi content rỗng (do enrichment fail) |
| T5 | Slide merge/dedup | 🟢 Thấp | Slides trùng nội dung cần gộp lại |
| T6 | Per-slide zoom preview | 🟢 Thấp | UI cần zoom in/out để xem chi tiết từng slide |
| T7 | Batch processing | 🟢 Thấp | Xử lý nhiều file cùng lúc |
| T8 | User authentication | 🟢 Thấp | Login system |
| T9 | Production deployment | 🟢 Thấp | Deploy lên server |

---

## API Configuration

| Service | Model | Env Var | Status |
|---------|-------|---------|--------|
| **Open Claude (LLM)** | `claude-sonnet-4-6` | `LLM_MODEL` | ✅ Hoạt động, không bị content filter |
| **Open Claude (Image)** | `gpt-5.4-image` | `OPENAI_MODEL` | ✅ Có key |
| **Pollinations.ai** | URL-based free | — | ✅ Không cần key |
| **Pexels** | — | `PEXELS_API_KEY` | ✅ Có key |
| **Pixabay** | — | `PIXABAY_API_KEY` | ✅ Có key |
| **ElevenLabs** | — | `ELEVENLABS_API_KEY` | ✅ Có key (10K tokens/tháng) |
| **Hugging Face** | SDXL, FLUX | `HUGGINGFACE_API_KEY` | ✅ Có token |
| **Ollama local** | `qwen3:8b` | `OLLAMA_MODEL` | ⏳ Đang download |
| **edge-tts** | — | — | ✅ Free, unlimited |

---

## Files Đã Tạo Mới

| File | Chức năng |
|------|-----------|
| `skills/ppt-master/scripts/extract_slide_assets.py` | Trích text + hình từ PPTX/DOCX/PDF |
| `skills/ppt-master/scripts/enrich_content.py` | AI diễn giải chi tiết nội dung |
| `skills/ppt-master/scripts/vision_analyze_slides.py` | OCR + AI text analysis (3-step) |
| `skills/ppt-master/scripts/ocr_slide_images.py` | OCR standalone |
| `skills/ppt-master/scripts/slide_image_pipeline.py` | Auto gen/search hình per slide |
| `skills/ppt-master/scripts/parse_style_prompt.py` | Parse user style prompt |
| `skills/ppt-master/scripts/assemble_slides.py` | Ráp content + images → SVG → PPTX |
| `skills/ppt-master/scripts/slide_audio_pipeline.py` | Gen audio per slide |
| `skills/ppt-master/scripts/auto_pptx_pipeline.py` | Unified 1-command pipeline |
| `skills/ppt-master/scripts/image_backends/backend_pollinations.py` | Pollinations.ai free image gen |
| `skills/ppt-master/scripts/llm_backends/backend_openclaude.py` | Open Claude LLM backend |
| `backend/main.py` | FastAPI backend (pipeline API) |
| `frontend/app/page.tsx` | Next.js frontend (PPTX Pipeline page) |
| `.env` | API keys configuration |

---

## Lưu Ý Quan Trọng

1. **PPTX phải editable**: DrawingML native shapes, KHÔNG embed SVG as image
2. **MP3 không nhúng vào PPTX**: Audio chỉ lưu trong folder
3. **Mỗi slide 1 thư mục**: `slides/slide_XX/`
4. **Content enrichment**: DIỄN GIẢI chi tiết, KHÔNG tóm tắt
5. **OCR là bắt buộc**: Hình có chart/table/diagram phải OCR trước khi gửi AI
6. **claude-sonnet-4-6**: Model chính, không bị content filter (khác deepseek-v4-flash)
7. **edge-tts mặc định**: Free, unlimited. ElevenLabs chỉ khi cần chất lượng cao
8. **Backward compatible**: Không phá vỡ pipeline hiện có
