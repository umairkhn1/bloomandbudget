#!/usr/bin/env python3
"""Three Pinterest directions for one post. Run: python3 _build/make_pin_variants.py"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageOps

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "_build"))
from make_pins import fraunces, inter, peony_disc, CREAM, INK, ROSE, SAGE, MUTED, LINE  # noqa: E402

W, H = 1000, 1500
OUT = ROOT / "img" / "pins"
SRC = Path("/app/conversations/6adddb3001a84324ecbc714e/work/cover-square.png")


def letterspace(d, x, y, text, font, fill, track=7.0):
    for ch in text.upper():
        d.text((x, y), ch, font=font, fill=fill)
        x += d.textlength(ch, font=font) + track
    return x


def wordmark(d, x, y, size=30, color=INK):
    f = fraunces(size, wght=600, opsz=30)
    for t, c in (("Bloom ", color), ("&", ROSE), (" Budget", color)):
        d.text((x, y), t, font=f, fill=c)
        x += d.textlength(t, font=f)
    return x


# ---------------------------------------------------------------- A: square photo, caption card
def variant_a():
    img = Image.new("RGB", (W, H), CREAM)
    shot = ImageOps.fit(Image.open(SRC).convert("RGB"), (W, 1000),
                        centering=(0.5, 0.45), method=Image.LANCZOS)
    img.paste(shot, (0, 0))
    d = ImageDraw.Draw(img)
    pad = 76

    letterspace(d, pad, 1032, "First apartment", inter(25, 600, 26), ROSE, 7.5)

    hf = fraunces(84, wght=600, opsz=90, soft=40)
    y = 1082
    for line in ("What moving out", "really costs"):
        d.text((pad, y), line, font=hf, fill=INK)
        y += 92

    d.line((pad, y + 10, pad + 120, y + 10), fill=ROSE, width=4)
    d.text((pad, y + 30), "The deposit is the cheap part.", font=inter(31, 500, 28), fill=MUTED)

    wordmark(d, pad, H - pad - 34, 30)
    uf = inter(25, 500, 26)
    t = "bloomandbudget.blog"
    d.text((W - pad - d.textlength(t, font=uf), H - pad - 28), t, font=uf, fill=MUTED)

    p = OUT / "pin-apartment-a-photo.png"; img.save(p); return p


# ---------------------------------------------------------------- B: full bleed, type on a scrim
def variant_b():
    shot = ImageOps.fit(Image.open(SRC).convert("RGB"), (W, H),
                        centering=(0.5, 0.58), method=Image.LANCZOS)
    img = shot.copy()
    d = ImageDraw.Draw(img)

    pad = 64
    card_top, card_bottom = 890, H - 64
    d.rounded_rectangle((pad, card_top, W - pad, card_bottom), radius=26, fill=CREAM)

    inner = pad + 52
    letterspace(d, inner, card_top + 56, "First apartment", inter(24, 600, 26), ROSE, 7.5)

    hf = fraunces(80, wght=600, opsz=90, soft=40)
    y = card_top + 104
    for line in ("What moving out", "really costs"):
        d.text((inner, y), line, font=hf, fill=INK)
        y += 88

    d.line((inner, y + 14, inner + 110, y + 14), fill=ROSE, width=4)
    d.text((inner, y + 34), "The deposit is the cheap part.",
           font=inter(30, 500, 28), fill=MUTED)

    wordmark(d, inner, card_bottom - 58, 27)
    uf = inter(23, 500, 26)
    t = "bloomandbudget.blog"
    d.text((W - inner - d.textlength(t, font=uf), card_bottom - 54), t, font=uf, fill=MUTED)

    p = OUT / "pin-apartment-b-overlay.png"; img.save(p); return p


# ---------------------------------------------------------------- C: the bill, on cream
def variant_c():
    img = Image.new("RGB", (W, H), CREAM)
    d = ImageDraw.Draw(img)
    pad = 88

    disc = peony_disc(112)
    img.paste(disc, (pad, pad - 6), disc)
    wordmark(d, pad + 128, pad + 24, 36)

    rows = [("Security deposit", "1,150"),
            ("First month's rent", "1,150"),
            ("Application fee", "50"),
            ("Renter's insurance", "15"),
            ("Furnishing an empty room", "1,380")]
    row_h = 96
    block = 62 + 208 + 44 + row_h * len(rows) + 12 + 30 + 74
    top, bottom = pad + 168, H - pad - 70
    y = top + max(0, (bottom - top - block) // 2)
    letterspace(d, pad, y, "The real bill", inter(27, 600, 26), ROSE, 9)
    y += 62

    hf = fraunces(96, wght=600, opsz=96, soft=40)
    for line in ("What moving out", "actually costs"):
        d.text((pad, y), line, font=hf, fill=INK)
        y += 104
    y += 44

    rf = inter(36, 500, 28)
    af = fraunces(46, wght=600, opsz=46)
    for label, amount in rows:
        d.text((pad, y), label, font=rf, fill=INK)
        aw = d.textlength(amount, font=af)
        d.text((W - pad - aw, y - 8), amount, font=af, fill=INK)
        lx = pad + d.textlength(label, font=rf) + 16
        rx = W - pad - aw - 16
        dot = lx
        while dot < rx - 4:
            d.ellipse((dot, y + 24, dot + 5, y + 29), fill=(204, 194, 178))
            dot += 15
        y += row_h

    y += 12
    d.line((pad, y, W - pad, y), fill=INK, width=3)
    y += 30
    tf = fraunces(52, wght=600, opsz=52)
    d.text((pad, y), "Before you sleep there", font=tf, fill=INK)
    tot = fraunces(64, wght=600, opsz=60)
    aw = d.textlength("$3,745", font=tot)
    d.text((W - pad - aw, y - 10), "$3,745", font=tot, fill=ROSE)

    uf = inter(27, 500, 26)
    d.text((pad, H - pad - 34), "bloomandbudget.blog", font=uf, fill=MUTED)
    note = "one person, $1,150 apartment"
    d.text((W - pad - d.textlength(note, font=uf), H - pad - 34), note, font=uf, fill=MUTED)

    p = OUT / "pin-apartment-c-bill.png"; img.save(p); return p


if __name__ == "__main__":
    for f in (variant_a, variant_b, variant_c):
        print(f())
