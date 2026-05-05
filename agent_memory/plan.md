c# PPT Master — Kế Hoạch Phát Triển (Final v4)

> Cập nhật: 2026-05-05
> Phân tích bởi: MiMo AI Agent

---

## Pipeline Tổng Quan

```
Input (PPTX/DOCX/PDF/Excel)
    │
    ▼
[Step 1] Trích xuất text + hình ảnh từ file cũ
    │   ├── ppt_to_md.py / doc_to_md.py / pdf_to_md.py / excel_to_md.py
    │   └── extract_slide_images.py (MỚI — tách hình embedded)
    │   ⚠️ Hình tách ra chỉ để THAM KHẢO / REUSE, KHÔNG bắt buộc AI phải xử lý
    │
    ▼
[Step 2] Cấu trúc hóa nội dung → JSON/Markdown từng slide riêng biệt
    │   └── structure_slide_content.py (MỚI — pure parsing, không cần AI)
    │
    ▼
[Step 3] AI xử lý nội dung: DIỄN GIẢI chi tiết (KHÔNG tóm tắt)
    │   ├── summarize_content.py → ĐỔI TÊN → enrich_content.py
    │   ├── LLM: kimi-k2.5 (Open Claude) hoặc Gemma4 local
    │   └── Input: JSON slide → Output: JSON slide đã diễn giải dễ hiểu
    │
    ▼
[Step 4] Tìm kiếm/Gen hình ảnh cho từng slide
    │   ├── image_search.py (Pexels, Pixabay — ảnh thật, free)
    │   ├── Pollinations.ai (AI gen, hoàn toàn free, không cần key)
    │   └── Open Claude gpt-5.4-image (AI gen, chất lượng cao)
    │
    ▼
[Step 5] Template system — user nhập prompt style
    │   ├── parse_style_prompt.py (MỚI — parse prompt user)
    │   └── assemble_slides.py (MỚI — ráp content + images → SVG)
    │
    ▼
[Step 6] Post-processing → Export PPTX editable
    │   ├── finalize_svg.py
    │   └── svg_to_pptx.py (DrawingML native)
    │
    ▼
[Step 7] Gen audio MP3 từng slide (tùy chọn)
    │   ├── notes_to_audio.py (đã có — gen từng file riêng)
    │   ├── Ưu tiên edge-tts (free, không giới hạn)
    │   └── ElevenLabs chỉ dùng khi cần chất lượng cao (limit 10K tokens/tháng)
    │
    ▼
Output: PPTX editable + mỗi slide 1 thư mục
```

---

## Phân Tích Từng Step & Giải Pháp

### Step 1: Extract Hình Ảnh Từ File Cũ

**Câu hỏi**: Tách hình embedded để làm gì? Nếu model không xử lý được thì sao?

**Giải pháp**:
- Hình tách ra **KHÔNG bắt buộc** model phải xử lý. Chúng chỉ là **tài liệu tham khảo**:
  - User muốn reuse hình cũ → có sẵn trong `sources/images/`
  - AI cần hiểu context slide (có hình gì) → đọc metadata JSON, KHÔNG đọc file hình
  - Hình cũ có thể dùng làm reference cho image search (tìm hình tương tự)
- **Nếu model crash**: Bỏ qua hoàn toàn bước extract hình. Pipeline vẫn chạy được chỉ với text. Extract hình là **optional enhancement**, không phải blocker.
- **Tách riêng**: Script `extract_slide_images.py` chạy độc lập, output ra `sources/images/`. Nếu fail, các step sau vẫn hoạt động bình thường.

**Kết luận**: KHÔNG crash pipeline. Hình là optional.

---

### Step 3: AI Xử Lý Nội Dung — DIỄN GIẢI, KHÔNG TÓM TẮT

**Câu hỏi**: Cần chi tiết nội dung, không phải tóm tắt rút gọn?

**Giải pháp**: Đổi tên script từ `summarize_content.py` → `enrich_content.py`

**Prompt template cho AI**:
```
Bạn là chuyên gia thiết kế bài giảng. Với nội dung slide sau, hãy DIỄN GIẢI 
chi tiết và dễ hiểu cho người học. KHÔNG được tóm tắt hay rút gọn.

Quy tắc:
1. Giữ lại TẤT CẢ thông tin quan trọng
2. Bổ sung giải thích, ví dụ minh họa nếu cần
3. Sử dụng ngôn ngữ đơn giản, dễ tiếp cận
4. Format: bullet points rõ ràng, có tiêu đề phụ
5. Nếu có dữ liệu số → giữ nguyên, thêm context giải thích
6. Mục tiêu: Người đọc slide này hiểu ngay nội dung mà không cần nghe giảng

Ví dụ:
- Input: "Con gà trống biết gáy"
- Output: "Con gà trống là con gà có thể gáy. Chỉ con gà trống mới biết gáy, 
  con gà mái không biết gáy. Tiếng gáy của gà trống thường vang vào buổi sáng sớm."

Nội dung slide cần diễn giải:
{slide_content}
```

**Xử lý khi model local crash**:
- **Gemma4 local**: Nếu file quá lớn (>8K tokens), chia thành từng slide riêng, gửi 1 slide/lần
- **kimi-k2.5 (Open Claude)**: Context window 128K tokens, xử lý thoải mái 30+ slides
- **Fallback cuối**: Nếu cả 2 model đều fail → giữ nguyên content gốc, đánh dấu `enriched: false` trong metadata

**Đảm bảo mỗi slide là 1 section riêng biệt**: ✅ Script `structure_slide_content.py` parse markdown → JSON array, mỗi element là 1 slide object. Step 6 sẽ iterate qua array này để generate từng SVG.

---

### Step 4: Free-Tier Image Generation Platforms

**Đã xác nhận hoạt động**:

| Platform | Free Tier | API | Chất lượng | Đăng ký |
|----------|-----------|-----|-----------|---------|
| **Pollinations.ai** | ✅ Hoàn toàn free, không giới hạn | URL GET | ⭐⭐⭐ | ❌ Không cần |
| **Pexels** | ✅ 200 req/hr | REST + key | ⭐⭐⭐⭐ | ✅ Đã có key |
| **Pixabay** | ✅ 100 req/min | REST + key | ⭐⭐⭐⭐ | ✅ Đã có key |

**Nên đăng ký thêm** (free tier, AI gen hình):

| Platform | Free Tier | API Style | Đăng ký | Models |
|----------|-----------|-----------|---------|--------|
| **Hugging Face Inference** | ✅ Free (rate limited) | REST API | https://huggingface.co/join | SDXL, FLUX-schnell, Stable Diffusion 3 |
| **Together.ai** | ✅ $1 credit (~200 ảnh) | OpenAI-compatible | https://api.together.xyz | FLUX-schnell, SDXL |
| **fal.ai** | ✅ Free tier | REST API | https://fal.ai | FLUX, Imagen3 |
| **Replicate** | ✅ Limited free | REST API | https://replicate.com | FLUX-1.1-pro, SDXL |
| **Stability AI** | ✅ Free credits | REST API | https://stability.ai | SDXL, SD3 |
| **Google AI Studio** | ✅ Free tier | REST API | https://aistudio.google.com | Gemini image gen |

**Khuyến nghị đăng ký** (theo thứ tự ưu tiên):
1. **Hugging Face** — free, nhiều models, không cần credit card
2. **Together.ai** — $1 free credit, OpenAI-compatible API
3. **Google AI Studio** — free tier, Gemini image gen

**Chiến lược image gen**:
```
1. Pexels/Pixabay search (ảnh thật, free, đã có key) ← Mặc định
2. Pollinations.ai (AI gen, free, không cần key) ← Khi cần ảnh minh họa
3. Hugging Face / Together.ai (AI gen, free tier) ← Khi cần chất lượng cao hơn
4. Open Claude gpt-5.4-image (AI gen, có key) ← Khi cần chất lượng tốt nhất
```

---

### Step 5: Template System — Chat-Based Style Input

**Câu hỏi**: Có thể nhập prompt style như chat không?

**Giải pháp**: Tạo script `parse_style_prompt.py` parse user prompt thành config

**Prompt format mẫu**:
```
[title] Làm slide về giáo dục
[style] lấy màu đen làm chủ đạo, nền galaxy
[font] tiêu đề Montserrat bold 36pt, nội dung Open Sans 18pt
[layout] slide đầu tiên hình nền full, các slide sau chia 2 cột
[icon] sử dụng icon phẳng, style line
[image] tìm hình liên quan đến giáo dục, công nghệ
[language] tiếng Việt
[pages] 8-10 slides
```

**Script parse_style_prompt.py**:
- Input: user prompt string
- Output: `style_config.json`
  ```json
  {
    "title": "Slide về giáo dục",
    "colors": {
      "primary": "#000000",
      "secondary": "#1a1a2e",
      "accent": "#4a90d9",
      "background": "galaxy_gradient"
    },
    "fonts": {
      "heading": "Montserrat Bold",
      "heading_size": 36,
      "body": "Open Sans",
      "body_size": 18
    },
    "layout": {
      "cover": "full_image",
      "content": "two_column"
    },
    "icons": "flat_line",
    "image_search": "giáo dục, công nghệ",
    "language": "vi",
    "page_count": {"min": 8, "max": 10}
  }
  ```
- Nếu user không nhập đủ field → dùng default values
- Nếu user nhập tự nhiên (không có [tag]) → dùng AI parse

**Prompt mẫu cho user**:
```
# Format cơ bản
[title] Tiêu đề bài thuyết trình
[style] Mô tả phong cách (màu sắc, nền, cảm giác)
[font] Font tiêu đề + font nội dung
[layout] Cách bố trí slide
[icon] Style icon
[image] Mô tả hình ảnh mong muốn
[language] Ngôn ngữ
[pages] Số lượng slide

# Ví dụ
[title] Giới thiệu sản phẩm mới
[style] hiện đại, gradient xanh dương, nền trắng sạch sẽ
[font] tiêu đề Poppins bold 32pt, nội dung Roboto 16pt
[layout] slide đầu full hình, còn lại chia cột trái phải
[icon] icon phẳng, 2 tông màu
[image] sản phẩm công nghệ, thiết bị điện tử
[language] tiếng Việt
[pages] 10 slides
```

---

### Step 7: Audio Generation — Cơ Chế Chi Tiết

**Cơ chế hiện tại** (đã có trong `notes_to_audio.py`):
1. Đọc `notes/*.md` — mỗi file là 1 slide (đã được `total_md_split.py` tách từ `notes/total.md`)
2. Extract spoken text (bỏ heading markdown)
3. **Gen từng file riêng**: mỗi slide → 1 file `.mp3` riêng biệt
4. Output: `audio/slide_01.mp3`, `audio/slide_02.mp3`, ...
5. **KHÔNG gen 1 file lớn** — đã đúng design

**Flow chi tiết**:
```
notes/total.md (tất cả speaker notes)
    │
    ▼ total_md_split.py
notes/slide_01.md, slide_02.md, ... (mỗi slide 1 file)
    │
    ▼ notes_to_audio.py (iterate từng file)
audio/slide_01.mp3, slide_02.mp3, ... (mỗi slide 1 mp3)
```

**ElevenLabs — Limit 10K tokens/tháng**:

| Provider | Free Limit | Chi phí | Khuyến nghị |
|----------|-----------|---------|-------------|
| **edge-tts** | ✅ Không giới hạn | Miễn phí | **Ưu tiên 1** — dùng mặc định |
| **ElevenLabs** | 10K tokens/tháng (~10 phút audio) | Miễn phí (free tier) | Chỉ dùng khi cần voice chất lượng cao |
| **MiniMax** | Có free tier | Tùy plan | Backup |
| **Qwen TTS** | Có free tier | Tùy plan | Backup |

**Chiến lược audio**:
- **Mặc định**: edge-tts (free, không giới hạn, tiếng Việt tốt)
- **ElevenLabs**: Chỉ dùng cho bài thuyết trình quan trọng, limit ~10 slides (10K tokens ≈ 10 phút)
- **Tính toán token**: 1 slide ≈ 100-200 tokens → 10K tokens ≈ 50-100 slides (vừa đủ cho 1 bài)
- **Nếu vượt limit**: Tự động fallback về edge-tts

**Đảm bảo slide và mp3 match**:
- File naming convention: `slide_01.md` → `slide_01.mp3`
- Script iterate theo thứ tự file, KHÔNG random
- Metadata JSON ghi rõ slide_number → audio_file mapping

---

## Subtasks Chi Tiết (Clean Version)

### SUBTASK 1: Tích hợp API Keys ✅

**Trạng thái**: ĐÃ HOÀN THÀNH

**Files**: `.env`

---

### SUBTASK 2: Tích hợp Open Claude LLM + Pollinations.ai Image Gen

**Trạng thái**: CHƯA BẮT ĐẦU

**Mục tiêu**: 
- Backend sử dụng kimi-k2.5 qua Open Claude cho content enrichment
- Thêm Pollinations.ai làm free image gen backend

**Công việc**:
1. Tạo `skills/ppt-master/scripts/llm_backends/backend_openclaude.py`
   - OpenAI-compatible format
   - Base URL: `https://open-claude.com/v1`
   - Model: `kimi-k2.5`
2. Tạo `skills/ppt-master/scripts/image_backends/backend_pollinations.py`
   - URL-based API: `GET https://image.pollinations.ai/prompt/{encoded_prompt}`
   - Params: width, height, nologo, seed
   - Download image từ response
3. Cập nhật `backend/main.py`
   - Thêm `openai-compatible` provider cho LLM
   - Đọc config từ `.env`
4. Cập nhật `image_gen.py`
   - Thêm `pollinations` backend vào `BACKEND_REGISTRY`

**Files liên quan**:
- MỚI: `skills/ppt-master/scripts/llm_backends/backend_openclaude.py`
- MỚI: `skills/ppt-master/scripts/image_backends/backend_pollinations.py`
- SỬA: `backend/main.py`, `skills/ppt-master/scripts/image_gen.py`

**Ước tính**: 3-4 giờ

---

### SUBTASK 3: Extract Hình Ảnh + Metadata Từ File Cũ

**Trạng thái**: CHƯA BẮT ĐẦU

**Mục tiêu**: Tách hình embedded + metadata từ PPTX/DOCX/PDF. OPTIONAL — không crash pipeline nếu fail.

**Công việc**:
1. Tạo `skills/ppt-master/scripts/extract_slide_assets.py`
   - Input: file PPTX/DOCX/PDF
   - Output:
     - `sources/images/slide_XX_image_YY.png` (hình extracted)
     - `sources/slide_metadata.json` (metadata từng slide)
   - Dùng `python-pptx` cho PPTX, `PyMuPDF` cho PDF
   - **Error handling**: Nếu extract fail → log warning, tiếp tục pipeline với text only
2. Metadata JSON format:
   ```json
   [
     {
       "slide_number": 1,
       "title": "Slide Title",
       "content_raw": "Full text content...",
       "images_extracted": ["slide_01_image_01.png"],
       "layout_hint": "title_slide|content|image_heavy|data|closing"
     }
   ]
   ```

**Files liên quan**:
- MỚI: `skills/ppt-master/scripts/extract_slide_assets.py`

**Ước tính**: 2-3 giờ

---

### SUBTASK 4: Cấu Trúc Hóa + Diễn Giải Nội Dung

**Trạng thái**: CHƯA BẮT ĐẦU

**Mục tiêu**: 
- Parse markdown → JSON có cấu trúc slide riêng biệt
- AI diễn giải chi tiết (KHÔNG tóm tắt) nội dung từng slide

**Công việc**:
1. Tạo `skills/ppt-master/scripts/structure_slide_content.py`
   - Input: markdown file (từ Step 1)
   - Output: `slides_structured.json`
   - Pure parsing logic, KHÔNG cần AI
   - Parse headers → slide boundaries
   - Mỗi slide là 1 object riêng biệt
   - Detect slide type: title, content, image_text, data, closing

2. Tạo `skills/ppt-master/scripts/enrich_content.py`
   - Input: `slides_structured.json`
   - Output: `slides_enriched.json`
   - **DIỄN GIẢI chi tiết**, KHÔNG tóm tắt
   - Prompt: "Giải thích dễ hiểu, bổ sung ví dụ, giữ tất cả thông tin"
   - Xử lý từng slide riêng (1 slide/lần gọi LLM)
   - Fallback: nếu LLM fail → giữ nguyên content gốc
   - Token management: mỗi slide ~500-1000 tokens input + output

3. Đảm bảo output JSON format:
   ```json
   [
     {
       "slide_number": 1,
       "type": "title",
       "title": "Giáo dục STEM",
       "content": "Nội dung đã diễn giải chi tiết...",
       "bullet_points": ["Điểm 1", "Điểm 2"],
       "enriched": true,
       "image_hint": "hình ảnh liên quan đến giáo dục STEM"
     }
   ]
   ```

**Files liên quan**:
- MỚI: `skills/ppt-master/scripts/structure_slide_content.py`
- MỚI: `skills/ppt-master/scripts/enrich_content.py`

**Ước tính**: 3-4 giờ

---

### SUBTASK 5: Per-Slide Image Pipeline

**Trạng thái**: CHƯA BẮT ĐẦU

**Mục tiêu**: Tự động tìm/gen hình ảnh phù hợp cho từng slide

**Công việc**:
1. Tạo `skills/ppt-master/scripts/slide_image_pipeline.py`
   - Input: `slides_enriched.json` + config
   - Output: `slides/slide_XX/images/`
   - Logic:
     - Đọc `image_hint` từ enriched JSON
     - Sinh search query hoặc image prompt
     - Chọn mode:
       - `--mode search`: Pexels/Pixabay (mặc định)
       - `--mode pollinations`: Pollinations.ai (free AI gen)
       - `--mode ai`: Open Claude gpt-5.4-image (chất lượng cao)
       - `--mode auto`: search trước, nếu không có → pollinations
     - Lưu hình vào per-slide folder
     - Tạo `image_mapping.json`

**Files liên quan**:
- MỚI: `skills/ppt-master/scripts/slide_image_pipeline.py`

**Ước tính**: 3-4 giờ

---

### SUBTASK 6: Template System + Slide Assembler

**Trạng thái**: CHƯA BẮT ĐẦU

**Mục tiêu**: 
- User nhập prompt style → parse thành config
- Ráp content + images → SVG → PPTX editable

**Công việc**:
1. Tạo `skills/ppt-master/scripts/parse_style_prompt.py`
   - Input: user prompt string
   - Output: `style_config.json`
   - Parse [title], [style], [font], [layout], [icon], [image], [language], [pages]
   - Default values cho missing fields
   - Nếu input tự nhiên → dùng AI parse

2. Tạo `skills/ppt-master/scripts/assemble_slides.py`
   - Input: `slides_enriched.json` + `image_mapping.json` + `style_config.json`
   - Output: `svg_output/slide_XX.svg`
   - Chọn layout dựa trên slide type + user style
   - Generate SVG với hình embedded
   - Áp dụng colors, fonts, spacing từ style_config

3. Chạy post-processing:
   - `finalize_svg.py` → `svg_to_pptx.py`

**Files liên quan**:
- MỚI: `skills/ppt-master/scripts/parse_style_prompt.py`
- MỚI: `skills/ppt-master/scripts/assemble_slides.py`

**Ước tính**: 5-6 giờ

---

### SUBTASK 7: Unified Pipeline Script

**Trạng thái**: CHƯA BẮT ĐẦU

**Mục tiêu**: 1 command chạy toàn bộ pipeline

**Công việc**:
1. Tạo `skills/ppt-master/scripts/auto_pptx_pipeline.py`
   - Usage:
     ```bash
     python3 scripts/auto_pptx_pipeline.py <input_file> \
       --style "[title] Giáo dục [style] nền galaxy, màu đen chủ đạo" \
       --image-mode search \
       --llm openclaude \
       --tts edge \
       --output-dir projects/my_presentation
     ```
   - Pipeline: Step 1 → 2 → 3 → 4 → 5 → 6 → (optional 7)
   - Progress logging từng step
   - Error handling: retry, fallback, skip

2. Output structure:
   ```
   projects/my_presentation/
   ├── sources/
   │   ├── original.pptx
   │   ├── extracted.md
   │   └── images/                 # Hình từ file gốc (optional)
   ├── slides/
   │   ├── slide_01/
   │   │   ├── content.md
   │   │   ├── content.json        # Structured + enriched data
   │   │   ├── images/             # Gen/searched images
   │   │   ├── audio.mp3           # (Optional) TTS audio
   │   │   └── metadata.json
   │   └── slide_N/
   ├── svg_output/
   ├── svg_final/
   ├── exports/
   │   └── presentation.pptx       # Final PPTX (editable)
   ├── style_config.json
   ├── design_spec.md
   └── spec_lock.md
   ```

**Files liên quan**:
- MỚI: `skills/ppt-master/scripts/auto_pptx_pipeline.py`

**Ước tính**: 3-4 giờ

---

### SUBTASK 8: Audio Pipeline (Optional)

**Trạng thái**: CHƯA BẮT ĐẦU

**Mục tiêu**: Gen audio MP3 từng slide, match chính xác với nội dung

**Cơ chế**:
```
slides_enriched.json (nội dung từng slide)
    │
    ▼ Tạo notes/slide_XX.md từ enriched content
notes/slide_01.md, slide_02.md, ...
    │
    ▼ notes_to_audio.py (gen từng file)
audio/slide_01.mp3, slide_02.mp3, ...
    │
    ▼ Copy vào per-slide folder
slides/slide_01/audio.mp3, slides/slide_02/audio.mp3, ...
```

**ElevenLabs token management**:
- Free tier: 10K tokens/tháng
- Ước tính: 1 slide ≈ 100-200 tokens → ~50-100 slides/tháng
- **Strategy**: 
  - Mặc định dùng edge-tts (free, không giới hạn)
  - ElevenLabs chỉ dùng khi user chọn explicitly
  - Nếu gần hết limit → warning + fallback edge-tts
  - Tính toán trước: estimate total tokens trước khi gen

**Công việc**:
1. Tạo `skills/ppt-master/scripts/slide_audio_pipeline.py`
   - Input: `slides_enriched.json` + TTS config
   - Tạo `notes/slide_XX.md` từ enriched content
   - Gọi `notes_to_audio.py` cho từng slide
   - Copy audio vào `slides/slide_XX/audio.mp3`
   - Token counting cho ElevenLabs

**Files liên quan**:
- MỚI: `skills/ppt-master/scripts/slide_audio_pipeline.py`
- DÙNG: `skills/ppt-master/scripts/notes_to_audio.py`

**Ước tính**: 2-3 giờ

---

### SUBTASK 9: Backend API + Frontend UI

**Trạng thái**: CHƯA BẮT ĐẦU

**Công việc**:
1. Backend API:
   - `POST /api/pipeline/run` — trigger full pipeline
   - `GET /api/pipeline/status/{id}` — check progress
   - `GET /api/templates` — list templates
   - `GET /api/projects/{name}/slides` — list slides
2. Frontend:
   - Pipeline page: upload → nhập style prompt → run
   - Slide editor: preview + edit per slide
   - Export page: download PPTX

**Ước tính**: 6-8 giờ

---

### SUBTASK 10: Testing & QA

**Trạng thái**: CHƯA BẮT ĐẦU

**Test cases**:
- [ ] PPTX extraction: text + images
- [ ] Content enrichment: diễn giải chi tiết, không tóm tắt
- [ ] Image search: Pexels/Pixabay trả hình phù hợp
- [ ] Image gen: Pollinations.ai gen hình OK
- [ ] Style prompt parsing: user input → config JSON
- [ ] Assembly: SVG đúng layout, hình embedded
- [ ] PPTX export: editable trong PowerPoint
- [ ] Audio: edge-tts gen mp3 từng slide, match nội dung
- [ ] ElevenLabs: token counting, fallback khi hết limit
- [ ] Unified pipeline: 1 command chạy hết

**Ước tính**: 2-3 giờ

---

## Ưu Tiên & Timeline

| Priority | Subtask | Task | Est. | Dependencies |
|----------|---------|------|------|--------------|
| ✅ Done | 1 | API Keys | — | — |
| 🔴 P0 | 2 | Open Claude + Pollinations.ai | 3-4h | Subtask 1 |
| 🔴 P0 | 3 | Extract hình + metadata | 2-3h | — |
| 🔴 P0 | 4 | Cấu trúc hóa + diễn giải nội dung | 3-4h | Subtask 2 |
| 🔴 P0 | 5 | Per-slide image pipeline | 3-4h | Subtask 4 |
| 🔴 P0 | 6 | Template system + assembler | 5-6h | Subtask 4, 5 |
| 🔴 P0 | 7 | Unified pipeline | 3-4h | Subtask 2-6 |
| 🟡 P1 | 8 | Audio pipeline | 2-3h | Subtask 4 |
| 🟡 P1 | 9 | Backend + Frontend UI | 6-8h | Subtask 7 |
| 🟢 P2 | 10 | Testing & QA | 2-3h | Subtask 7-9 |

**Tổng**: 29-39 giờ

---

## API Configuration

| Service | Key (xem trong `.env`) | Model | Purpose |
|---------|------------------------|-------|---------|
| **Open Claude** | `OPENCLAUDE_API_KEY` | `kimi-k2.5` | LLM: diễn giải nội dung |
| **Open Claude** | (same) | `gpt-5.4-image` | Image gen (chất lượng cao) |
| **Pollinations.ai** | ❌ Không cần (URL-based free) | — | Image gen (free, unlimited) |
| **Pexels** | `PEXELS_API_KEY` | — | Image search |
| **Pixabay** | `PIXABAY_API_KEY` | — | Image search |
| **Hugging Face** | `HUGGINGFACE_API_KEY` | SDXL, FLUX-schnell | Image gen (free tier) |
| **ElevenLabs** | `ELEVENLABS_API_KEY` | — | TTS (limit 10K tokens/tháng) |
| **edge-tts** | ❌ Không cần | — | TTS (free, unlimited) ← mặc định |

---

## Lưu Ý Quan Trọng

1. **PPTX editable**: DrawingML native shapes, KHÔNG embed SVG as image
2. **MP3 không nhúng vào PPTX**: Audio chỉ lưu trong folder
3. **Mỗi slide 1 thư mục**: `slides/slide_XX/`
4. **Content enrichment**: DIỄN GIẢI chi tiết, KHÔNG tóm tắt
5. **Image là optional**: Pipeline không crash nếu extract/gen image fail
6. **Audio ưu tiên edge-tts**: ElevenLabs chỉ khi cần, limit 10K tokens/tháng
7. **Backward compatible**: Không phá vỡ pipeline hiện có
