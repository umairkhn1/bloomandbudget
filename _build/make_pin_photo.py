#!/usr/bin/env python3
"""Photo-led Pinterest pins (1000x1500): a real cover photo on top, the money
promise underneath. Run: python3 _build/make_pin_photo.py"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageOps

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "_build"))
from make_pins import fraunces, inter, peony_disc, CREAM, INK, ROSE, SAGE, MUTED, LINE, W, H  # noqa: E402

OUT = ROOT / "img" / "pins"


def photo_pin(photo, eyebrow, hero, sub, specs, cta, slug, photo_h=760, hero_size=150):
    """Every block advances by its measured ink box, so nothing can collide."""
    pad = 78
    img = Image.new("RGB", (W, H), CREAM)

    shot = ImageOps.fit(Image.open(ROOT / photo).convert("RGB"),
                        (W, photo_h), centering=(0.5, 0.42), method=Image.LANCZOS)
    img.paste(shot, (0, 0))
    fade = 230
    grad = Image.new("L", (1, fade))
    for i in range(fade):
        grad.putpixel((0, i), int(255 * (i / (fade - 1)) ** 1.8))
    img.paste(Image.new("RGB", (W, fade), CREAM), (0, photo_h - fade), grad.resize((W, fade)))

    d = ImageDraw.Draw(img)
    boxes = []

    def put(x, y, text, font, fill):
        d.text((x, y), text, font=font, fill=fill)
        b = d.textbbox((x, y), text, font=font)
        boxes.append((text[:18], b))
        return b

    # eyebrow, letterspaced
    ef = inter(26, wght=600, opsz=26)
    y = photo_h + 30
    tx = pad
    for ch in eyebrow.upper():
        d.text((tx, y), ch, font=ef, fill=ROSE)
        tx += d.textlength(ch, font=ef) + 7.5
    boxes.append(("eyebrow", d.textbbox((pad, y), eyebrow.upper(), font=ef)))
    y += 46

    b = put(pad, y, hero, fraunces(hero_size, wght=600, opsz=120, soft=40), INK)
    y = b[3] + 34

    b = put(pad, y, sub, fraunces(46, wght=500, opsz=60, soft=40), ROSE)
    y = b[3] + 48

    d.line((pad, y, W - pad, y), fill=LINE, width=2)
    y += 32

    nf = fraunces(44, wght=600, opsz=48, soft=40)
    lf = inter(21, wght=500, opsz=24)
    col = (W - pad * 2) // len(specs)
    for i, (num, label) in enumerate(specs):
        cx = pad + col * i
        put(cx, y, num, nf, INK)
        put(cx, y + 58, label, lf, MUTED)

    # cta + footer
    cf = inter(32, wght=600, opsz=26)
    cta_w = d.textlength(cta, font=cf)
    pill_h, pill_y = 82, H - pad - 120
    d.rounded_rectangle((pad, pill_y, pad + cta_w + 84, pill_y + pill_h),
                        radius=pill_h // 2, fill=INK)
    d.text((pad + 42, pill_y + (pill_h - 36) // 2 - 3), cta, font=cf, fill=CREAM)

    disc = peony_disc(44)
    img.paste(disc, (pad, pill_y + pill_h + 26), disc)
    put(pad + 60, pill_y + pill_h + 32, "bloomandbudget.blog", inter(28, 500, 26), MUTED)
    wf = fraunces(30, wght=600, opsz=30)
    tw = d.textlength("Bloom & Budget", font=wf)
    put(W - pad - tw, pill_y + pill_h + 30, "Bloom & Budget", wf, INK)

    # collision check
    for i, a in enumerate(boxes):
        for b2 in boxes[i + 1:]:
            ax0, ay0, ax1, ay1 = a[1]; bx0, by0, bx1, by1 = b2[1]
            if ax0 < bx1 and bx0 < ax1 and ay0 < by1 and by0 < ay1:
                print(f"  !! overlap: {a[0]!r} {a[1]} vs {b2[0]!r} {b2[1]}")
    print("  last text bottom:", max(b[1][3] for b in boxes), "| pill top:", pill_y)

    OUT.mkdir(parents=True, exist_ok=True)
    p = OUT / f"pin-{slug}.png"
    img.save(p)
    return p


if __name__ == "__main__":
    photo_pin(
        photo="img/cover-first-apartment.png",
        eyebrow="Moving out",
        hero="$3,745",
        sub="before you sleep there",
        specs=[("$1,150", "deposit"),
               ("$1,150", "first month"),
               ("$1,380", "to furnish it")],
        cta="See the full bill",
        slug="first-apartment-cost",
    )
