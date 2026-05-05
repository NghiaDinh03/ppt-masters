# PPT Master — Repository Context & Analysis

> Last updated: 2026-05-04
> Analyzed by: MiMo AI Agent

---

## 1. Project Overview

**PPT Master** is an AI-driven presentation generation system that converts source documents (PDF, DOCX, XLSX, PPTX, URL, Markdown) into **natively editable PowerPoint (PPTX)** files with real DrawingML shapes, text boxes, and charts — not embedded images.

- **Version**: v2.5.0
- **License**: MIT
- **Author**: Hugo He (何雨果) — Finance professional (CPA · CPV · Consulting Engineer)
- **Repository**: https://github.com/hugohe3/ppt-master
- **Live Demo**: https://hugohe3.github.io/ppt-master/

### Core Value Proposition
- **Real PowerPoint output** — every element is clickable and editable in PowerPoint
- **Transparent cost** — free and open source; only cost is AI model usage
- **Data stays local** — entire pipeline runs on user's machine (except AI API calls)
- **No platform lock-in** — works with Claude Code, Cursor, VS Code Copilot, Codex, etc.

---

## 2. Technology Stack

### 2.1 Core Runtime
| Technology | Version | Purpose |
|---|---|---|
| **Python** | 3.10+ | Core runtime — the only required dependency |
| **SVG** | 1.1 | Intermediate format for slide generation (AI generates SVG → post-processing converts to DrawingML) |
| **DrawingML (OOXML)** | — | Native PowerPoint shape format — final output |

### 2.2 Python Dependencies (from `skills/ppt-master/requirements.txt`)

#### SVG to PPTX Conversion
| Package | Purpose |
|---|---|
| `python-pptx>=0.6.21` | Batch-convert SVG files to PowerPoint presentations |
| `svglib>=1.5.0` | SVG parsing and conversion (lightweight fallback) |
| `reportlab>=4.0.0` | PDF/graphics library used by svglib |
| `cairosvg` (optional) | Full gradient/filter SVG-to-PNG support |

#### Source Document Conversion
| Package | Purpose |
|---|---|
| `PyMuPDF>=1.23.0` | PDF to Markdown conversion |
| `mammoth>=1.6.0` | DOCX to Markdown (native Python) |
| `markdownify>=0.11.6` | HTML to Markdown |
| `ebooklib>=0.18` | EPUB to Markdown |
| `nbconvert>=7.0.0` | Jupyter Notebook to Markdown |
| `openpyxl>=3.1.0` | Excel (.xlsx/.xlsm) to Markdown |

#### Web Scraping
| Package | Purpose |
|---|---|
| `requests>=2.31.0` | HTTP requests |
| `beautifulsoup4>=4.12.0` | HTML parsing |
| `curl_cffi>=0.7.0` | TLS fingerprint impersonation (for WeChat, etc.) |

#### Image Processing
| Package | Purpose |
|---|---|
| `Pillow>=9.0.0` | Image manipulation |
| `numpy>=1.20.0` | Numerical operations for image processing |

#### AI Image Generation
| Package | Purpose |
|---|---|
| `google-genai>=1.0.0` | Gemini image generation backend |
| `openai>=1.0.0` | OpenAI-compatible image generation backend |

#### Audio/TTS
| Package | Purpose |
|---|---|
| `edge-tts>=7.2.8` | Microsoft Edge neural TTS (default, no API key needed) |

#### Web Editor
| Package | Purpose |
|---|---|
| `flask>=3.0.0` | Localhost SVG editor server |

### 2.3 External Tools (Optional)
| Tool | When Needed |
|---|---|
| **Node.js 18+** | WeChat article import when `curl_cffi` unavailable |
| **Pandoc** | Legacy format conversion (.doc, .odt, .rtf, .tex, .rst, .org, .typ) |

---

## 3. AI/LLM Integration

### 3.1 Supported AI Agents (IDE/CLI)
| Type | Examples |
|---|---|
| **IDE-native agent** | Cursor, Trae, Codebuddy IDE, Windsurf, Void, Zed |
| **IDE plugin/extension** | GitHub Copilot, Claude Code (VS Code/JetBrains), Cline, Continue, Roo Code |
| **CLI agent** | Claude Code CLI, Codex CLI, Aider, Gemini CLI |

### 3.2 Recommended LLM Models
| Model | Notes |
|---|---|
| **Claude Opus / Sonnet** | Recommended and most tested — best SVG layout precision |
| **GPT series** | Newer versions (GPT-5.5+) improved; older versions had layout issues |
| **Gemini** | Variable quality |
| **Kimi, MiniMax, GLM** | Variable quality; models with stronger frontend/visual capabilities work better |

### 3.3 AI Image Generation Backends
| Backend | Model Examples | API Key Required |
|---|---|---|
| **OpenAI** | gpt-image-2 | Yes |
| **Gemini** | gemini-3.1-flash-image-preview | Yes |
| **Qwen (通义)** | qwen-image-2.0-pro | Yes |
| **Zhipu (智谱)** | glm-image | Yes |
| **Volcengine (火山引擎)** | doubao-seedream-4-5 | Yes |
| **MiniMax** | image-01 | Yes |
| **Stability AI** | stable-image-core | Yes |
| **BFL (FLUX)** | flux-pro-1.1-ultra | Yes |
| **Ideogram** | ideogram-v3 | Yes |
| **SiliconFlow** | Qwen/Qwen-Image | Yes |
| **FAL** | fal-ai/imagen3/fast | Yes |
| **Replicate** | black-forest-labs/flux-1.1-pro | Yes |
| **OpenRouter** | google/gemini-3.1-flash-image-preview | Yes |
| **ModelScope** | Tongyi-MAI/Z-Image-Turbo | Yes |

### 3.4 TTS (Text-to-Speech) Backends
| Backend | Voice Cloning | API Key |
|---|---|---|
| **edge-tts** (default) | ❌ | No key needed |
| **ElevenLabs** | ✅ | Yes |
| **MiniMax** | ✅ | Yes |
| **Qwen TTS** | ✅ | Yes |
| **CosyVoice** | ✅ | Yes |

### 3.5 Web Image Search Sources
| Source | API Key | Notes |
|---|---|---|
| **Openverse** | No key | Open-licensed images |
| **Wikimedia Commons** | No key | Open-licensed images |
| **Pexels** | Yes (free) | Stock photography |
| **Pixabay** | Yes (free) | Stock photography |

---

## 4. Architecture & Pipeline

### 4.1 Core Pipeline
```
Source Document → Create Project → Template Option → Strategist Eight Confirmations
    → [Image_Generator] → Executor → Quality Check → Post-processing → Export PPTX
```

### 4.2 Multi-Role Collaboration
| Role | Responsibility |
|---|---|
| **Strategist** | Content analysis, design planning, Eight Confirmations, outputs `design_spec.md` + `spec_lock.md` |
| **Image_Generator** | AI image generation or web image search (conditional) |
| **Executor** | SVG page generation (Visual Construction → Quality Check → Logic Construction) |

### 4.3 Three-Stage Technical Pipeline
1. **Stage 1 — Content Understanding & Design Planning**: Source docs → Markdown → Strategist analysis → Design Specification
2. **Stage 2 — AI Visual Generation**: Executor generates each slide as SVG
3. **Stage 3 — Engineering Conversion**: Post-processing converts SVG → DrawingML (native PPTX shapes)

### 4.4 Why SVG as Intermediate Format?
- SVG and DrawingML share the same worldview: absolute-coordinate 2D vector graphics
- AI can reliably generate SVG
- Humans can preview/debug SVG in any browser
- Scripts can precisely convert SVG to DrawingML
- Alternatives considered and rejected: Direct DrawingML (too verbose), HTML/CSS (structural mismatch), WMF/EMF (no AI training data), SVG as embedded images (destroys editability)

---

## 5. Key Scripts & Tools

### 5.1 Source Content Conversion
| Script | Purpose |
|---|---|
| `scripts/source_to_md/pdf_to_md.py` | PDF → Markdown |
| `scripts/source_to_md/doc_to_md.py` | DOCX/HTML/EPUB/IPYNB → Markdown (native); .doc/.odt/.rtf/.tex/.rst/.org/.typ (pandoc fallback) |
| `scripts/source_to_md/excel_to_md.py` | Excel (.xlsx/.xlsm) → Markdown |
| `scripts/source_to_md/ppt_to_md.py` | PowerPoint → Markdown |
| `scripts/source_to_md/web_to_md.py` | Web page → Markdown |
| `scripts/source_to_md/web_to_md.cjs` | Node.js fallback for WeChat/TLS-blocked sites |

### 5.2 Project Management
| Script | Purpose |
|---|---|
| `scripts/project_manager.py` | Project init, import-sources, validate, info |
| `scripts/project_utils.py` | Shared utilities, canvas format definitions |

### 5.3 Image Tools
| Script | Purpose |
|---|---|
| `scripts/analyze_images.py` | Image analysis |
| `scripts/image_gen.py` | AI image generation (multi-provider) |
| `scripts/image_search.py` | Web image search (Openverse, Wikimedia, Pexels, Pixabay) |
| `scripts/gemini_watermark_remover.py` | Remove Gemini-generated watermarks |
| `scripts/rotate_images.py` | Image rotation |

### 5.4 SVG Processing
| Script | Purpose |
|---|---|
| `scripts/svg_quality_checker.py` | SVG quality validation |
| `scripts/finalize_svg.py` | SVG post-processing (unified entry) |
| `scripts/svg_position_calculator.py` | Chart coordinate calculation |
| `scripts/update_spec.py` | Propagate spec_lock changes across SVGs |

### 5.5 PPTX Export
| Script | Purpose |
|---|---|
| `scripts/svg_to_pptx.py` | SVG → PPTX conversion (thin wrapper) |
| `scripts/svg_to_pptx/` | Full package: DrawingML converter, PPTX builder, animations, narration |
| `scripts/pptx_animations.py` | PowerPoint animation support |
| `scripts/pptx_template_import.py` | Template import |

### 5.6 Audio/Narration
| Script | Purpose |
|---|---|
| `scripts/notes_to_audio.py` | Speaker notes → audio narration |
| `scripts/total_md_split.py` | Split speaker notes per slide |

### 5.7 SVG Editor
| Script | Purpose |
|---|---|
| `scripts/svg_editor/server.py` | Flask-based localhost SVG editor |
| `scripts/svg_editor/static/` | Frontend (HTML/JS/CSS) |

---

## 6. Supported Canvas Formats

| Format | Code | Dimensions | Use Case |
|---|---|---|---|
| 16:9 Presentation | `ppt169` | 1920×1080 | Standard widescreen (default) |
| 4:3 Presentation | `ppt43` | 1456×1092 | Traditional presentation |
| Xiaohongshu (RED) | `xhs` | 1242×1660 | Social media image posts |
| WeChat Moments | `moments` | 1080×1080 | Square social posts |
| Story/TikTok | `story` | 1080×1920 | Vertical stories |
| WeChat Article Header | `wechat-header` | 900×383 | Article cover images |
| A4 Print | `a4` | 2480×3508 | Print posters, flyers |

---

## 7. Executor Styles

| Style | Focus | Target Audience |
|---|---|---|
| **General Versatile** | Visual impact first | Public / clients / trainees |
| **General Consulting** | Data clarity first | Teams / management |
| **Top Consulting (MBB)** | Logical persuasion first | Executives / board |

---

## 8. Icon Libraries

| Library | Style | Character |
|---|---|---|
| `chunk-filled` | Fill, straight-line geometry | Sharp, heavy, architectural |
| `tabler-filled` | Fill, bezier curves | Smooth, rounded, organic |
| `tabler-outline` | Stroke (line art) | Airy, refined, lightweight |
| `phosphor-duotone` | Duotone (main + 20% backplate) | Layered, contemporary |
| Brand logos | Various brand icons | Brand-specific |

---

## 9. Standalone Workflows

| Workflow | Path | Purpose |
|---|---|---|
| `create-template` | `workflows/create-template.md` | Standalone template creation |
| `verify-charts` | `workflows/verify-charts.md` | Chart coordinate calibration |
| `visual-edit` | `workflows/visual-edit.md` | Browser-based visual editor |
| `generate-audio` | `workflows/generate-audio.md` | Audio narration generation |
| `topic-research` | `workflows/topic-research.md` | Topic research |

---

## 10. Project Structure

```
ppt-masters/
├── AGENTS.md                    # Agent entry point
├── CLAUDE.md                    # Claude-specific instructions
├── README.md                    # English documentation
├── README_CN.md                 # Chinese documentation
├── requirements.txt             # Root requirements (delegates to skill)
├── .env.example                 # Environment configuration template
├── index.html                   # Live demo / showcase page
├── docs/                        # Documentation
│   ├── *.md                     # English docs
│   ├── zh/                      # Chinese docs
│   ├── assets/                  # Images, screenshots
│   └── rules/                   # Code style, prompt style rules
├── skills/
│   └── ppt-master/
│       ├── SKILL.md             # Main workflow authority
│       ├── requirements.txt     # Python dependencies
│       ├── .env.example         # Skill-level env config
│       ├── references/          # Role definitions & tech specs
│       ├── scripts/             # All runnable tools
│       ├── templates/           # Layout templates, chart templates, icons
│       └── workflows/           # Standalone workflow definitions
├── examples/                    # Example projects (22 projects, 309 pages)
├── projects/                    # User project workspace
└── .claude-plugin/              # Claude Code plugin marketplace config
```

---

## 11. Docker Compose Analysis

### Current Status: ❌ No Docker/Docker Compose files exist

The repository does **not** contain any `Dockerfile`, `docker-compose.yml`, or `.dockerignore` files. The only Docker reference is an SVG icon file (`templates/icons/simple-icons/docker.svg`).

### Feasibility Assessment
Creating a Docker Compose setup is **feasible** but has considerations:

**What Docker would need:**
- Python 3.10+ base image
- `pip install -r requirements.txt`
- Optional: Node.js for WeChat fallback, Pandoc for legacy formats
- Cairo system dependencies for CairoSVG (optional)

**Challenges:**
- The tool is designed as a **CLI/workflow tool** that runs inside AI IDEs (Claude Code, Cursor, etc.), not as a standalone service
- No web server or API endpoint to expose (except the optional Flask SVG editor)
- The pipeline requires an AI agent to orchestrate — Docker alone can't run the full workflow
- Image generation and TTS require external API keys

**Docker could be useful for:**
- Standardizing the Python environment
- Running the post-processing scripts (`finalize_svg.py`, `svg_to_pptx.py`)
- Running the SVG editor server
- Batch processing existing projects

---

## 12. Chinese Text Inventory (Needs Translation)

### Files with Chinese text in Python scripts:
| File | Chinese Content |
|---|---|
| `scripts/config.py` | Canvas format names (小红书) |
| `scripts/project_utils.py` | Format aliases (小红书, 朋友圈), legacy file names (设计规范与内容大纲.md, 来源文档.md) |
| `scripts/source_to_md/web_to_md.py` | Chinese date/URL patterns, site name suffixes |
| `scripts/source_to_md/pdf_to_md.py` | Chinese date patterns, heading patterns |
| `scripts/total_md_split.py` | Chinese page number patterns (第X页) |
| `scripts/template_import/manifest.py` | Chinese keywords (致谢, 谢谢, 感谢, 目录, 议程, 章节) |
| `scripts/tts_backends/backend_edge.py` | Chinese voice descriptions |
| `scripts/image_sources/provider_common.py` | Chinese infrastructure terms (地铁, 站, 轨道) |

### Documentation files:
| Path | Language |
|---|---|
| `README_CN.md` | Chinese |
| `docs/zh/*.md` | Chinese (6 files) |
| `docs/*.md` | English (already) |
| `skills/ppt-master/references/*.md` | English (already) |
| `skills/ppt-master/SKILL.md` | English (already) |

---

## 13. Feasibility for User's Word/PPT Processing Requirement

### User's Requirement:
> Use AI to process Word files → Extract key information → Output structured storyboard as PDF/PPT/Docs

### Analysis:

**✅ What PPT Master already supports:**
- DOCX → Markdown conversion (`doc_to_md.py`)
- PPTX → Markdown conversion (`ppt_to_md.py`)
- LLM reads Markdown and generates structured presentations
- Output as natively editable PPTX
- Speaker notes generation
- Multiple output formats (16:9, 4:3, social media, etc.)

**⚠️ What needs adaptation:**
- The current pipeline generates **visual presentations** (SVG → PPTX), not **text-based storyboards**
- The user wants a **summary/storyboard** format, not a full visual presentation
- Need to add: Markdown → structured PDF/DOCX export (text-based, not visual)
- Need to add: numbered headers with `fields: value` structure
- Need to add: clean formatting with proper fonts, tables, colors

**🔧 Recommended approach:**
1. Use existing `doc_to_md.py` / `ppt_to_md.py` for input conversion
2. Use LLM to read Markdown and extract/summarize key information
3. Add a new export path: structured Markdown → PDF/DOCX (using `python-docx` or `reportlab`)
4. Format with numbered headers, tables, proper typography

**📦 Additional dependencies needed:**
- `python-docx` — for DOCX output
- `reportlab` — for PDF output (already in requirements as transitive dependency)
- `weasyprint` or `markdown-pdf` — for Markdown → PDF with styling

---

## 14. Environment Configuration

### Required Environment Variables (for image generation):
```
IMAGE_BACKEND=openai|gemini|qwen|zhipu|volcengine|minimax|...
OPENAI_API_KEY=sk-xxx
GEMINI_API_KEY=xxx
QWEN_API_KEY=xxx
# ... etc.
```

### Optional Environment Variables:
```
PEXELS_API_KEY=xxx        # Stock photo search
PIXABAY_API_KEY=xxx       # Stock photo search
ELEVENLABS_API_KEY=xxx    # Voice cloning TTS
MINIMAX_API_KEY=xxx       # MiniMax TTS
QWEN_API_KEY=xxx          # Qwen TTS
COSYVOICE_API_KEY=xxx     # CosyVoice TTS
```

### Config Resolution Order:
1. `./.env` in current working directory
2. `<repo-root>/.env` (when running from a clone)
3. `~/.ppt-master/.env` (user-level config)

---

## 15. Quick Start Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Convert source documents
python3 skills/ppt-master/scripts/source_to_md/pdf_to_md.py <PDF_file>
python3 skills/ppt-master/scripts/source_to_md/doc_to_md.py <DOCX_file>
python3 skills/ppt-master/scripts/source_to_md/excel_to_md.py <XLSX_file>
python3 skills/ppt-master/scripts/source_to_md/ppt_to_md.py <PPTX_file>
python3 skills/ppt-master/scripts/source_to_md/web_to_md.py <URL>

# Project management
python3 skills/ppt-master/scripts/project_manager.py init <project_name> --format ppt169
python3 skills/ppt-master/scripts/project_manager.py import-sources <project_path> <source_files...> --move
python3 skills/ppt-master/scripts/project_manager.py validate <project_path>

# Image tools
python3 skills/ppt-master/scripts/analyze_images.py <project_path>/images
python3 skills/ppt-master/scripts/image_gen.py "prompt" --aspect_ratio 16:9 --image_size 1K -o <project_path>/images
python3 skills/ppt-master/scripts/svg_quality_checker.py <project_path>

# Post-processing pipeline
python3 skills/ppt-master/scripts/total_md_split.py <project_path>
python3 skills/ppt-master/scripts/finalize_svg.py <project_path>
python3 skills/ppt-master/scripts/svg_to_pptx.py <project_path>
```
