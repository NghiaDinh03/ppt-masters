#!/usr/bin/env python3
"""
Slide Audio Pipeline — Gen audio MP3 cho từng slide

Input: slides_enriched.json
Output: slides/slide_XX/audio.mp3

Usage:
    python3 slide_audio_pipeline.py <project_path> --provider edge --voice vi-VN-HoaiMyNeural
    python3 slide_audio_pipeline.py <project_path> --provider elevenlabs --voice-id <id>
"""

import sys
import os
import json
import subprocess
from pathlib import Path


# Windows console encoding fix
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))


def generate_slide_audio(project_path: Path, provider: str = "edge", voice: str = None, voice_id: str = None) -> dict:
    """Generate audio for each slide.

    Args:
        project_path: Project directory with slides_enriched.json
        provider: TTS provider ("edge", "elevenlabs", "minimax", "qwen", "cosyvoice")
        voice: Voice name (for edge-tts)
        voice_id: Voice ID (for cloud providers)

    Returns:
        Audio mapping dict.
    """
    enriched_path = project_path / "slides_enriched.json"
    if not enriched_path.exists():
        raise FileNotFoundError(f"slides_enriched.json not found")

    slides = json.loads(enriched_path.read_text(encoding="utf-8"))
    print(f"[audio] Generating audio for {len(slides)} slides, provider={provider}")

    # Create notes directory with per-slide files
    notes_dir = project_path / "notes"
    notes_dir.mkdir(exist_ok=True)

    for slide in slides:
        num = slide.get("slide_number", 0)
        content = slide.get("content", slide.get("content_raw", ""))
        title = slide.get("title", "")

        # Create note file (skip headings, keep spoken text)
        spoken = f"{title}. {content}" if title else content
        # Clean markdown
        spoken = spoken.replace("**", "").replace("##", "").replace("#", "")
        spoken = spoken.replace("- ", "").replace("* ", "")

        note_path = notes_dir / f"slide_{num:02d}.md"
        note_path.write_text(spoken.strip(), encoding="utf-8")

    # Write total.md
    total = "\n\n".join(
        f"## Slide {s.get('slide_number', 0)}\n\n{s.get('content', s.get('content_raw', ''))}"
        for s in slides
    )
    (notes_dir / "total.md").write_text(total, encoding="utf-8")

    # Call notes_to_audio.py
    scripts_dir = Path(__file__).resolve().parent
    audio_script = scripts_dir / "notes_to_audio.py"

    if not audio_script.exists():
        print("[audio] notes_to_audio.py not found, skipping audio generation")
        return {}

    # Build command
    cmd = [sys.executable, str(audio_script), str(project_path)]

    if provider == "edge":
        if not voice:
            voice = "vi-VN-HoaiMyNeural"
        cmd.extend(["--voice", voice, "--rate", "+0%"])
    elif provider == "elevenlabs":
        if not voice_id:
            print("[audio] Error: --voice-id required for elevenlabs")
            return {}
        cmd.extend(["--provider", "elevenlabs", "--voice-id", voice_id])
    elif provider == "minimax":
        if not voice_id:
            voice_id = "male-qn-qingse"
        cmd.extend(["--provider", "minimax", "--voice-id", voice_id])
    elif provider == "qwen":
        if not voice_id:
            voice_id = "Chelsie"
        cmd.extend(["--provider", "qwen", "--voice-id", voice_id])
    elif provider == "cosyvoice":
        if not voice_id:
            voice_id = "longxiaocheng"
        cmd.extend(["--provider", "cosyvoice", "--voice-id", voice_id])

    print(f"[audio] Running: {' '.join(cmd[:6])}...")
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(scripts_dir.parent.parent))

    if result.returncode != 0:
        print(f"[audio] Error: {result.stderr[:500]}")
        return {}

    print(f"[audio] {result.stdout.strip()}")

    # Copy audio files to per-slide folders
    audio_dir = project_path / "audio"
    audio_mapping = {}

    for slide in slides:
        num = slide.get("slide_number", 0)
        slide_dir = project_path / "slides" / f"slide_{num:02d}"
        slide_dir.mkdir(parents=True, exist_ok=True)

        # Find audio file
        for ext in [".mp3", ".wav", ".flac"]:
            src = audio_dir / f"slide_{num:02d}{ext}"
            if src.exists():
                dst = slide_dir / f"audio{ext}"
                import shutil
                shutil.copy2(str(src), str(dst))
                audio_mapping[f"slide_{num:02d}"] = str(dst)
                print(f"[audio]   Slide {num}: {dst.name}")
                break

    # Save mapping
    mapping_path = project_path / "audio_mapping.json"
    mapping_path.write_text(json.dumps(audio_mapping, ensure_ascii=False, indent=2), encoding="utf-8")

    return audio_mapping


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate audio for each slide")
    parser.add_argument("project_path", help="Project directory")
    parser.add_argument("--provider", default="edge", choices=["edge", "elevenlabs", "minimax", "qwen", "cosyvoice"],
                        help="TTS provider (default: edge)")
    parser.add_argument("--voice", default=None, help="Voice name (for edge-tts)")
    parser.add_argument("--voice-id", default=None, help="Voice ID (for cloud providers)")
    args = parser.parse_args()

    project_path = Path(args.project_path)
    if not project_path.exists():
        print(f"Error: Directory not found: {project_path}", file=sys.stderr)
        return 1

    generate_slide_audio(project_path, args.provider, args.voice, args.voice_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
