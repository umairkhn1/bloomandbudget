#!/usr/bin/env python3
"""Build vertical Pinterest pins (1000x1500) in the Bloom & Budget palette.

Run: python3 _build/make_pins.py
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT  = ROOT / "img" / "pins"
PEONY = ROOT / "img" / "brand-src" / "peony.png"
FONTS = Path("/app/conversations/6adddb3001a84324ecbc714e/logo/fonts")
if not FONTS.exists():                      # fallback for a clean checkout
    FONTS = ROOT / "img" / "pins" / "fonts"
FR, IN = FONTS / "fraunces-var.ttf", FONTS / "inter-var.ttf"

W, H = 1000, 1500
CREAM, INK = (250, 246, 240), (34, 57, 43)
ROSE, SAGE, MUTED = (168, 90, 60), (111, 139, 122), (102, 117, 104)
LINE = (219, 210, 196)


def fraunces(size, wght=600, opsz=72, soft=35, wonk=1):
    f = ImageFont.truetype(str(FR), size); f.set_variation_by_axes([opsz, wght, soft, wonk]); return f


def inter(size, wght=600, opsz=24):
    f = ImageFont.truetype(str(IN), size); f.set_variation_by_axes([opsz, wght]); return f


def wrap(draw, text, font, width):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=font) <= width:
            cur = t
        else:
            lines.append(cur); cur = w
    if cur:
        lines.append(cur)
    return lines


def peony_disc(px, zoom=1.15):
    ss = 4; d = px * ss
    im = Image.open(PEONY).convert("RGB")
    side = int(min(im.size) / zoom)
    im = im.crop(((im.width - side) // 2, (im.height - side) // 2,
                  (im.width + side) // 2, (im.height + side) // 2)).resize((d, d), Image.LANCZOS)
    out = Image.new("RGBA", (d, d), (0, 0, 0, 0))
    m = Image.new("L", (d * 4, d * 4), 0)
    ImageDraw.Draw(m).ellipse((0, 0, d * 4 - 1, d * 4 - 1), fill=255)
    out.paste(im, (0, 0), m.resize((d, d), Image.LANCZOS))
    dr = ImageDraw.Draw(out)
    w = max(2, int(d * 0.020))
    dr.ellipse((w // 2, w // 2, d - 1 - w // 2, d - 1 - w // 2), outline=SAGE, width=w)
    return out.resize((px, px), Image.LANCZOS)


def pin(eyebrow, headline, rows, cta, slug, headline_size=104, number_size=178,
        label_size=36, row_h=200):
    """Numbers are the hero; everything is placed from measured text metrics."""
    pad = 78
    inner = W - pad * 2
    img = Image.new("RGB", (W, H), CREAM)
    d = ImageDraw.Draw(img)

    # masthead
    disc = peony_disc(116)
    img.paste(disc, (pad, pad), disc)
    wf = fraunces(48, wght=600, opsz=40)
    bx, by = pad + 116 + 22, pad + 14
    for txt, col in (("Bloom ", INK), ("&", ROSE), (" Budget", INK)):
        d.text((bx, by), txt, font=wf, fill=col); bx += d.textlength(txt, font=wf)
    top = pad + 116 + 50

    # CTA from the bottom
    cf = inter(34, wght=600, opsz=26)
    cta_w = d.textlength(cta, font=cf)
    pill_h, pill_y = 90, H - pad - 118
    bottom = pill_y + pill_h + 30

    # measured body
    ef = inter(27, wght=600, opsz=26); track = 7.0
    hf = fraunces(headline_size, wght=600, opsz=96, soft=40)
    lines = wrap(d, headline, hf, inner)
    rf = fraunces(number_size, wght=600, opsz=120, soft=40)
    lf = inter(label_size, wght=500, opsz=28)

    num_w = max(d.textlength(n, font=rf) for n, _ in rows)
    label_x = pad + int(num_w) + 44
    body_h = 34 + 26 + 34 + int(headline_size*1.16)*len(lines) + 46 + row_h*len(rows) + 2
    y = top + max(36, int((pill_y - top - body_h) / 2))
    print(f"  body {body_h}px  y {y}..{y+body_h}  pill {pill_y}")

    tx = pad
    for ch in eyebrow.upper():
        d.text((tx, y), ch, font=ef, fill=ROSE); tx += d.textlength(ch, font=ef) + track
    y += 34 + 26

    for ln in lines:
        d.text((pad, y), ln, font=hf, fill=INK); y += int(headline_size*1.16)
    y += 46

    for num, label in rows:
        d.line((pad, y, W-pad, y), fill=LINE, width=2)
        d.text((pad, y + 6), num, font=rf, fill=SAGE)
        d.text((label_x, y + row_h//2 - label_size//2), label, font=lf, fill=INK)
        y += row_h
    d.line((pad, y, W-pad, y), fill=LINE, width=2)

    pill_w = cta_w + 88
    d.rounded_rectangle((pad, pill_y, pad+pill_w, pill_y+pill_h), radius=pill_h//2, fill=INK)
    d.text((pad+44, pill_y + (pill_h-38)//2 - 3), cta, font=cf, fill=CREAM)
    d.text((pad, pill_y+pill_h+30), "bloomandbudget.blog", font=inter(31,500,26), fill=MUTED)

    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"pin-{slug}.png"; img.save(path)
    return path


if __name__ == "__main__":
    p = pin(
        eyebrow="First salary",
        headline="Where your first paycheck goes",
        rows=[("62%", "Rent, food, transit, debt"),
              ("20%", "Moved to savings on payday"),
              ("18%", "Fun money, on purpose")],
        cta="Read the system",
        slug="budget-first-salary",
    )
    print(p, Image.open(p).size)
