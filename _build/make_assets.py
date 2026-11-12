#!/usr/bin/env python3
"""Generate derived assets: WebP covers, per-page OG cards, author
placeholder, template preview and the printable budget PDF.

Run: python3 _build/make_assets.py
"""

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "_build"
IMG = ROOT / "img"

CREAM = (250, 246, 240)
INK = (34, 57, 43)
INK_SOFT = (76, 95, 82)
ROSE_DARK = (168, 90, 60)
MUTED = (102, 117, 104)

SERIF_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
SANS_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def font(path, size):
    return ImageFont.truetype(path, size)


def fit(img, size):
    return ImageOps.fit(img, size, centering=(0.5, 0.45), method=Image.LANCZOS)


def cover_webp(src, dest, size):
    img = Image.open(ROOT / "img" / src).convert("RGB")
    fit(img, size).save(ROOT / "img" / dest, "WEBP", quality=84, method=6)


def wrap(draw, text, fnt, max_width):
    words = text.split()
    lines, current = [], ""
    for word in words:
        trial = (current + " " + word).strip()
        if draw.textlength(trial, font=fnt) <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def og_card(base_image, dest, title, eyebrow):
    W, H = 1200, 630
    img = fit(Image.open(base_image).convert("RGB"), (W, H))
    wash = Image.new("RGBA", (W, H), CREAM + (232,))
    img = Image.alpha_composite(img.convert("RGBA"), wash)
    draw = ImageDraw.Draw(img)

    # left rule
    draw.rectangle([0, 0, 14, H], fill=ROSE_DARK)

    pad = 84
    eyebrow_font = font(SANS_BOLD, 24)
    draw.text((pad, 78), eyebrow.upper(), font=eyebrow_font, fill=ROSE_DARK)

    size = 62
    while size > 34:
        title_font = font(SERIF_BOLD, size)
        lines = wrap(draw, title, title_font, W - pad * 2)
        if len(lines) <= 4:
            break
        size -= 4
    title_font = font(SERIF_BOLD, size)
    lines = wrap(draw, title, title_font, W - pad * 2)
    y = 152
    for line in lines:
        draw.text((pad, y), line, font=title_font, fill=INK)
        y += int(size * 1.28)

    # footer wordmark
    draw.text((pad, H - 96), "Bloom & Budget", font=font(SERIF_BOLD, 30), fill=INK)
    draw.text((pad + 300, H - 90), "bloomandbudget.com",
              font=font(SANS, 22), fill=MUTED)

    img.convert("RGB").save(dest, "JPEG", quality=82, optimize=True, progressive=True)


def author_placeholder(dest):
    S = 800
    img = Image.new("RGB", (S, S), CREAM)
    draw = ImageDraw.Draw(img)
    draw.ellipse([80, 80, S - 80, S - 80], fill=(231, 239, 232))
    f = font(SERIF_BOLD, 210)
    text = "EJ"
    w = draw.textlength(text, font=f)
    draw.text(((S - w) / 2, S / 2 - 130), text, font=f, fill=INK)
    f2 = font(SANS, 26)
    cap = "replace with a photo"
    w2 = draw.textlength(cap, font=f2)
    draw.text(((S - w2) / 2, S - 220), cap, font=f2, fill=MUTED)
    dest.parent.mkdir(parents=True, exist_ok=True)
    img.save(dest, "JPEG", quality=88)


def template_preview(dest):
    """A mock of the printable worksheet, so the page shows what you get."""
    W, H = 1000, 1294
    img = Image.new("RGB", (W, H), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    pad = 70

    draw.rectangle([0, 0, W, 8], fill=ROSE_DARK)
    draw.text((pad, 70), "MONTHLY BUDGET", font=font(SANS_BOLD, 20), fill=ROSE_DARK)
    draw.text((pad, 104), "Month: ______________", font=font(SERIF_BOLD, 34), fill=INK)
    draw.line([pad, 170, W - pad, 170], fill=(232, 224, 211), width=2)

    y = 200
    sections = [
        ("INCOME", ["Take-home pay", "Other income"]),
        ("THE FOUR WALLS", ["Rent / mortgage", "Utilities", "Groceries",
                            "Transport", "Minimum debt payments"]),
        ("FLEXIBLE SPENDING", ["Fun money", "Eating out", "Shopping",
                               "Subscriptions", "Other"]),
        ("SAVINGS", ["Emergency fund", "Sinking funds", "Long-term savings"]),
    ]
    for title, rows in sections:
        draw.text((pad, y), title, font=font(SANS_BOLD, 17), fill=ROSE_DARK)
        y += 30
        draw.text((W - pad - 250, y - 28), "PLANNED", font=font(SANS_BOLD, 12), fill=MUTED)
        draw.text((W - pad - 120, y - 28), "ACTUAL", font=font(SANS_BOLD, 12), fill=MUTED)
        for row in rows:
            draw.text((pad, y), row, font=font(SANS, 20), fill=INK)
            draw.line([W - pad - 130, y + 26, W - pad - 20, y + 26],
                      fill=(214, 205, 190), width=1)
            draw.line([W - pad - 270, y + 26, W - pad - 160, y + 26],
                      fill=(214, 205, 190), width=1)
            y += 44
        y += 18

    draw.rectangle([pad, H - 190, W - pad, H - 70], fill=(250, 246, 240))
    draw.text((pad + 24, H - 165), "A budget is a permission slip,",
              font=font(SERIF, 24), fill=INK_SOFT)
    draw.text((pad + 24, H - 128), "not a punishment.",
              font=font(SERIF, 24), fill=INK_SOFT)

    img.save(dest, "PNG", optimize=True)


def main():
    posts = json.loads((BUILD / "posts.json").read_text())
    cats = json.loads((BUILD / "categories.json").read_text())

    # 1. WebP versions of every cover + hero
    for post in posts:
        src = post["cover"].split("/")[-1].replace(".webp", "")
        png = Path(post["coverFallback"]).name
        cover_webp(png, src + ".webp", (1200, 750))
    cover_webp("hero.png", "hero.webp", (800, 880))

    # 2. per-page OG cards
    og = IMG / "og"
    og.mkdir(exist_ok=True)
    hero = IMG / "hero.png"

    og_card(hero, og / "home.jpg",
            "Grow your money while you grow up", "Bloom & Budget")
    og_card(hero, og / "about.jpg",
            "Hi, I'm Emma Jane", "About")
    og_card(hero, og / "blog.jpg",
            "Every post, newest first", "The archive")
    og_card(hero, og / "privacy.jpg",
            "Privacy Policy", "Legal")
    og_card(hero, og / "disclaimer.jpg",
            "Disclaimer: education, not advice", "Legal")
    og_card(hero, og / "terms.jpg",
            "Terms of Use", "Legal")
    og_card(hero, og / "free-budget-template.jpg",
            "Free printable monthly budget template", "Free download")
    og_card(hero, og / "not-found.jpg",
            "This page wandered off", "404")

    for cat in cats:
        og_card(hero, og / f"{cat['slug']}.jpg", cat["name"], "Category")

    for post in posts:
        base = IMG / post["cover"].split("/")[-1].replace(".webp", ".png")
        if not base.exists():
            base = next(IMG.glob(post["cover"].split("/")[-1].replace(".webp", ".*")))
        og_card(base, og / f"{post['slug']}.jpg", post["titlePlain"], post["category"])

    # 3. author placeholder + template preview
    author_placeholder(IMG / "author" / "emma-jane.jpg")
    template_preview(IMG / "template-preview.png")

    print("OG cards:", len(list(og.glob("*.jpg"))))
    print("done")


if __name__ == "__main__":
    main()
