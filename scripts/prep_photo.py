#!/usr/bin/env python3
"""
Prep a photo for ASCII conversion:
  1. Remove the background (rembg) so only the subject remains.
  2. Boost local contrast with CLAHE so a flat/evenly-lit face gets
     real highlights and shadows (otherwise it converts to a dark blob).
  3. Composite onto pure white, so background maps to the blank end
     of the ASCII ramp (white -> space character).
Output: source-prepped.png (grayscale) next to the input photo, in the repo root.
"""
import sys
import os

import cv2
import numpy as np
from PIL import Image
from rembg import remove, new_session

REPO_ROOT = os.path.join(os.path.dirname(__file__), "..")
OUT_PATH = os.path.join(REPO_ROOT, "source-prepped.png")

# u2netp is a much smaller/lighter model (~4MB) than the default (~1GB) —
# plenty accurate for a portrait silhouette cutout and far less memory-hungry.
_SESSION = new_session("u2netp")


def remove_background(input_path: str) -> Image.Image:
    with open(input_path, "rb") as f:
        input_bytes = f.read()
    output_bytes = remove(input_bytes, session=_SESSION)
    from io import BytesIO
    return Image.open(BytesIO(output_bytes)).convert("RGBA")


def composite_on_white(rgba_img: Image.Image) -> Image.Image:
    white_bg = Image.new("RGBA", rgba_img.size, (255, 255, 255, 255))
    composited = Image.alpha_composite(white_bg, rgba_img)
    return composited.convert("RGB")


def boost_contrast_clahe(pil_img: Image.Image) -> Image.Image:
    gray = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2GRAY)
    # Smaller tiles + higher clip limit pull out finer local contrast
    # (eyes, nose, mouth) that a flatly-lit face otherwise loses once
    # downsampled to a coarse ASCII grid.
    clahe = cv2.createCLAHE(clipLimit=3.5, tileGridSize=(4, 4))
    enhanced = clahe.apply(gray)
    # Light unsharp mask to keep facial-feature edges crisp through
    # the downsample-to-character-grid step.
    blurred = cv2.GaussianBlur(enhanced, (0, 0), 3)
    sharpened = cv2.addWeighted(enhanced, 1.6, blurred, -0.6, 0)
    return Image.fromarray(sharpened)


def crop_to_subject(rgba_img: Image.Image, padding_frac: float = 0.08) -> Image.Image:
    """Crop to the alpha-channel bounding box of the cutout subject, with
    a small padding margin, so the ASCII grid isn't wasted on empty space.
    Uses a fairly high alpha threshold since matting on hair/wisps leaves
    a faint low-alpha halo that can extend across most of the frame."""
    alpha = np.array(rgba_img.split()[-1])
    ys, xs = np.where(alpha > 180)
    if len(xs) == 0 or len(ys) == 0:
        return rgba_img
    x0, x1 = xs.min(), xs.max()
    y0, y1 = ys.min(), ys.max()
    w, h = rgba_img.size
    pad_x = int((x1 - x0) * padding_frac)
    pad_y = int((y1 - y0) * padding_frac)
    x0 = max(0, x0 - pad_x)
    y0 = max(0, y0 - pad_y)
    x1 = min(w, x1 + pad_x)
    y1 = min(h, y1 + pad_y)
    return rgba_img.crop((x0, y0, x1, y1))


def main():
    if len(sys.argv) < 2:
        print("Usage: python prep_photo.py <source-photo.jpg>", file=sys.stderr)
        sys.exit(1)

    input_path = sys.argv[1]
    if not os.path.exists(input_path):
        print(f"File not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    print("[prep_photo] Removing background...")
    rgba = remove_background(input_path)

    print("[prep_photo] Cropping to subject bounding box...")
    rgba = crop_to_subject(rgba)

    print("[prep_photo] Compositing onto white...")
    on_white = composite_on_white(rgba)

    print("[prep_photo] Boosting local contrast (CLAHE)...")
    final_gray = boost_contrast_clahe(on_white)

    final_gray.save(OUT_PATH)
    print(f"[prep_photo] Wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
