#!/usr/bin/env python3
"""
Pollinations.ai Image Generation Backend (FREE, no API key needed)

Generates images via Pollinations.ai URL-based API.
This is a completely free service that requires no authentication.

Usage via image_gen.py:
    IMAGE_BACKEND=pollinations python3 image_gen.py "a sunset" -o images/

Direct usage:
    python3 backend_pollinations.py "a sunset" -o images/

Configuration:
    POLLINATIONS_API_KEY  (optional) API key for priority access
"""

import sys
import os
import time
import urllib.parse
import requests

_SCRIPTS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from image_backends.backend_common import (
    download_image,
    resolve_output_path,
    save_image_bytes,
)


# Aspect ratio -> width/height mapping
ASPECT_RATIO_SIZE = {
    "1:1":  (1024, 1024),
    "16:9": (1024, 576),
    "9:16": (576, 1024),
    "4:3":  (1024, 768),
    "3:4":  (768, 1024),
    "3:2":  (1024, 683),
    "2:3":  (683, 1024),
    "21:9": (1024, 439),
}

IMAGE_SIZE_MAP = {
    "512px": 0.5,
    "1K": 1.0,
    "2K": 2.0,
    "4K": 4.0,
}


def generate(
    prompt: str,
    output_path: str,
    aspect_ratio: str = "16:9",
    image_size: str = "1K",
    seed: int = None,
    api_key: str = None,
    **kwargs,
) -> str:
    """Generate an image using Pollinations.ai free API.

    Args:
        prompt: Text description of the image to generate.
        output_path: File path to save the generated image.
        aspect_ratio: Image aspect ratio (e.g. "16:9", "1:1").
        image_size: Image size preset ("512px", "1K", "2K", "4K").
        seed: Optional seed for reproducibility.
        api_key: Optional API key (not required for free tier).

    Returns:
        Path to the saved image file.
    """
    # Parse aspect ratio to width/height
    base_w, base_h = ASPECT_RATIO_SIZE.get(aspect_ratio, (1024, 576))
    scale = IMAGE_SIZE_MAP.get(image_size, 1.0)
    width = int(base_w * scale)
    height = int(base_h * scale)

    # Build URL
    encoded_prompt = urllib.parse.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}"
    params = {
        "width": width,
        "height": height,
        "nologo": "true",
    }
    if seed is not None:
        params["seed"] = seed

    # Make request
    full_url = f"{url}?{'&'.join(f'{k}={v}' for k, v in params.items())}"
    print(f"[pollinations] Generating: {prompt[:60]}...")
    print(f"[pollinations] URL: {full_url[:120]}...")

    response = requests.get(full_url, timeout=120, stream=True)
    response.raise_for_status()

    # Save image
    content = response.content
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(content)

    print(f"[pollinations] Saved: {output_path} ({len(content)} bytes)")
    return output_path


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Pollinations.ai free image generation")
    parser.add_argument("prompt", help="Image description")
    parser.add_argument("-o", "--output", default=".", help="Output directory")
    parser.add_argument("--filename", default=None, help="Output filename")
    parser.add_argument("--aspect_ratio", default="16:9", help="Aspect ratio")
    parser.add_argument("--image_size", default="1K", help="Image size preset")
    parser.add_argument("--seed", type=int, default=None, help="Random seed")
    args = parser.parse_args()

    output_path = resolve_output_path(args.prompt, args.output, args.filename, ".jpg")
    generate(args.prompt, output_path, args.aspect_ratio, args.image_size, args.seed)
