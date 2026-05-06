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


def _clean_for_speech(text: str) -> str:
    """Clean text for natural speech output (TTS)."""
    import re
    # Remove markdown formatting
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # bold
    text = re.sub(r'\*(.*?)\*', r'\1', text)  # italic
    text = re.sub(r'#{1,6}\s*', '', text)  # headers
    text = re.sub(r'[-*•]\s+', '', text)  # bullets
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)  # links
    text = re.sub(r'`([^`]+)`', r'\1', text)  # code
    text = re.sub(r'\|', ',', text)  # table separators
    text = re.sub(r'---+', '.', text)  # horizontal rules
    text = re.sub(r'\n{2,}', '. ', text)  # multiple newlines
    text = re.sub(r'\n', ' ', text)  # single newlines
    text = re.sub(r'\s{2,}', ' ', text)  # multiple spaces
    text = re.sub(r'\.{2,}', '.', text)  # multiple dots
    text = text.strip()
    # Remove trailing punctuation duplicates
    if text and text[-1] in ',;':
        text = text[:-1] + '.'
    return text


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
        bullet_points = slide.get("bullet_points", [])
        summary = slide.get("summary", "")

        # Build clean spoken text
        spoken_parts = []

        # Add title as spoken intro
        if title and len(title) > 3:
            spoken_parts.append(f"{title}.")

        # Add summary first if available (most concise)
        if summary and len(summary) > 10:
            spoken_parts.append(summary)

        # Add bullet points (clean, structured)
        if bullet_points:
            for bp in bullet_points[:6]:
                bp_clean = _clean_for_speech(bp)
                if bp_clean and len(bp_clean) > 5:
                    spoken_parts.append(bp_clean)

        # If no bullets, use content
        if not spoken_parts or (len(spoken_parts) == 1 and title):
            content_clean = _clean_for_speech(content)
            if content_clean:
                spoken_parts.append(content_clean)

        # Join and limit length (avoid too long audio per slide)
        spoken = " ".join(spoken_parts)
        if len(spoken) > 1500:
            spoken = spoken[:1500] + "..."

        # Write clean text file (not markdown)
        txt_path = notes_dir / f"slide_{num:02d}.txt"
        txt_path.write_text(spoken.strip(), encoding="utf-8")

        # Also write markdown version for reference
        md_path = notes_dir / f"slide_{num:02d}.md"
        md_path.write_text(f"# {title}\n\n{content}", encoding="utf-8")

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
