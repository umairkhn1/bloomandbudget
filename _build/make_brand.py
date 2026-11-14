#!/usr/bin/env python3
"""Build the Bloom & Budget brand marks and favicons from the peony artwork.

Source of truth: img/brand-src/peony.png (original, commercially clean).
Outputs: img/brand/*.png and the whole img/favicon/ set.

Run: python3 _build/make_brand.py
"""
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
SRC  = ROOT / "img" / "brand-src" / "peony.png"
OUT  = ROOT / "img" / "brand"
FAV  = ROOT / "img" / "favicon"

SAGE  = (111, 139, 122)
CREAM = (250, 246, 240)


def circle_badge(px, zoom=1.12, ring=True):
    """Peony cropped to a circle with a sage ring, rendered 4x and downsampled."""
    ss = 4
    d = px * ss
    im = Image.open(SRC).convert("RGB")
    side = int(min(im.size) / zoom)
    im = im.crop(((im.width - side) // 2, (im.height - side) // 2,
                  (im.width + side) // 2, (im.height + side) // 2)).resize((d, d), Image.LANCZOS)
    out = Image.new("RGBA", (d, d), (0, 0, 0, 0))
    mask = Image.new("L", (d * 4, d * 4), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, d * 4 - 1, d * 4 - 1), fill=255)
    out.paste(im, (0, 0), mask.resize((d, d), Image.LANCZOS))
    if ring:
        dr = ImageDraw.Draw(out)
        w = max(2, int(d * 0.020))
        dr.ellipse((w // 2, w // 2, d - 1 - w // 2, d - 1 - w // 2), outline=SAGE, width=w)
        h = max(1, int(d * 0.005))
        dr.ellipse((w + h, w + h, d - 1 - w - h, d - 1 - w - h), outline=CREAM + (255,), width=h)
    return out.resize((px, px), Image.LANCZOS)


def touch_icon(px, pad_ratio=0.13):
    """Opaque cream square for iOS/Android home screens."""
    img = Image.new("RGBA", (px, px), CREAM)
    inner = int(px * (1 - 2 * pad_ratio))
    b = circle_badge(inner, zoom=1.12)
    img.paste(b, ((px - inner) // 2, (px - inner) // 2), b)
    return img.convert("RGB")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    FAV.mkdir(parents=True, exist_ok=True)

    for s in (128, 192, 512):
        circle_badge(s).save(OUT / f"peony-badge-{s}.png")

    for s in (16, 32, 48, 96, 144, 192):
        circle_badge(s, zoom=1.18).save(FAV / f"favicon-{s}.png")

    touch_icon(180).save(FAV / "apple-touch-icon.png")
    touch_icon(512).save(OUT / "app-icon-512.png")

    ico = circle_badge(256, zoom=1.18)
    ico.save(FAV / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)])
    print("brand marks + favicons written")


if __name__ == "__main__":
    main()
