#!/usr/bin/env python3
"""Audit the built site: internal links, anchors, headings, meta lengths,
images, leftover placeholders.

Run after _build/build.py: python3 _build/audit.py
Exits non-zero if anything is broken.
"""

import json
import re
import sys
import html as htmllib
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parent.parent
DOMAINS_OK = (json.loads((Path(__file__).parent / "config.json").read_text())["site"]["domain"],)

pages = {}
for path in sorted(ROOT.rglob("*.html")):
    rel = path.relative_to(ROOT).as_posix()
    if rel.startswith("docs/") or rel.startswith("google") or rel.startswith("_build/"):
        continue
    pages[rel] = path.read_text(encoding="utf-8")


def route_to_file(path):
    """Map a clean URL to the file Vercel would serve."""
    if path in ("", "/"):
        return "index.html"
    p = path.lstrip("/")
    if p.endswith("/"):
        p += "index.html"
    candidate = p if "." in p.rsplit("/", 1)[-1] else p + ".html"
    return candidate


STATIC_EXT = (".css", ".js", ".png", ".jpg", ".jpeg", ".webp", ".svg",
              ".ico", ".xml", ".txt", ".pdf", ".json", ".woff2")


def ids_in(doc):
    return set(re.findall(r'\sid="([^"]+)"', doc))


problems = []
warnings = []

# ---------------------------------------------------------------- links
anchors_cache = {rel: ids_in(doc) for rel, doc in pages.items()}

for rel, doc in pages.items():
    body = re.sub(r"<script.*?</script>", "", doc, flags=re.S)
    body = re.sub(r"<style.*?</style>", "", body, flags=re.S)
    for attr, target in re.findall(r'\s(href|src)="([^"]+)"', body):
        if target.startswith(("#", "mailto:", "tel:", "data:", "javascript:")):
            continue
        if re.match(r"^https?://", target):
            if target.startswith(DOMAINS_OK):
                local = target[len(DOMAINS_OK[0]):] or "/"
            else:
                continue  # external, not checked here
        else:
            local = target

        local, _, frag = local.partition("#")
        local = local.split("?")[0]
        local = unquote(local)
        if not local:
            continue
        if local.startswith("/"):
            target_file = route_to_file(local)
        else:
            target_file = (Path(rel).parent / local).as_posix()
            target_file = re.sub(r"^\./", "", target_file)
            target_file = Path(target_file).as_posix()
            if "." not in Path(target_file).name:
                target_file += ".html"

        if target_file.endswith(STATIC_EXT):
            if not (ROOT / target_file).exists():
                problems.append(f"{rel}: missing file {target} (looked for {target_file})")
            if attr == "src" and target_file.endswith((".png", ".jpg", ".webp")):
                size = (ROOT / target_file).stat().st_size
                if size > 400_000:
                    warnings.append(f"{rel}: heavy image {target_file} ({size // 1024} KB)")
            continue
        if target_file not in pages:
            problems.append(f"{rel}: broken {attr} -> {target} (looked for {target_file})")
            continue
        if frag and frag not in anchors_cache.get(target_file, set()):
            problems.append(f"{rel}: missing anchor #{frag} in {target_file}")

# ---------------------------------------------------------------- headings
for rel, doc in pages.items():
    h1s = re.findall(r"<h1[^>]*>(.*?)</h1>", doc, re.S)
    if len(h1s) != 1:
        problems.append(f"{rel}: {len(h1s)} h1 headings (expected 1)")
    order = [int(m) for m in re.findall(r"<h([1-6])[\s>]", doc)]
    prev = 1
    for level in order:
        if level - prev > 1:
            warnings.append(f"{rel}: heading jumps h{prev} -> h{level}")
        prev = level

# ---------------------------------------------------------------- meta
for rel, doc in pages.items():
    title = re.search(r"<title>(.*?)</title>", doc, re.S)
    desc = re.search(r'<meta name="description" content="([^"]*)"', doc)
    canon = re.search(r'<link rel="canonical" href="([^"]*)"', doc)
    og_url = re.search(r'<meta property="og:url" content="([^"]*)"', doc)
    og_img = re.search(r'<meta property="og:image" content="([^"]*)"', doc)

    if not title:
        problems.append(f"{rel}: no title")
    else:
        t = htmllib.unescape(title.group(1))
        if len(t) > 60:
            problems.append(f"{rel}: title {len(t)} chars (>60): {t}")
    if not desc:
        problems.append(f"{rel}: no meta description")
    else:
        d = htmllib.unescape(desc.group(1))
        if len(d) > 160:
            problems.append(f"{rel}: description {len(d)} chars (>160)")
        if len(d) < 50:
            warnings.append(f"{rel}: description only {len(d)} chars")
    if canon and og_url and canon.group(1) != og_url.group(1):
        problems.append(f"{rel}: canonical {canon.group(1)} != og:url {og_url.group(1)}")
    if rel == "404.html":
        continue
    if canon and "/404" in canon.group(1):
        problems.append(f"{rel}: canonical points at 404")
    if og_img:
        img_path = og_img.group(1).replace(DOMAINS_OK[0], "")
        if not (ROOT / img_path.lstrip("/")).exists():
            problems.append(f"{rel}: og:image missing on disk: {img_path}")

# ---------------------------------------------------------------- images
for rel, doc in pages.items():
    for img in re.findall(r"<img[^>]*>", doc):
        if "width=" not in img or "height=" not in img:
            problems.append(f"{rel}: img without width/height: {img[:80]}")
        if "loading=" not in img:
            problems.append(f"{rel}: img without loading attr: {img[:80]}")
        src = re.search(r'src="([^"]+)"', img)
        if src and src.group(1).startswith("/"):
            if not (ROOT / src.group(1).split("?")[0].lstrip("/")).exists():
                problems.append(f"{rel}: img not found: {src.group(1)}")
        alt = re.search(r'alt="([^"]*)"', img)
        decorative = 'aria-hidden="true"' in img
        if not alt or (not alt.group(1).strip() and not decorative):
            problems.append(f"{rel}: img without alt: {img[:80]}")

# ---------------------------------------------------------------- leftovers
RETIRED_HOSTS = ("bloomandbudget.com",)
for rel, doc in pages.items():
    for bad in RETIRED_HOSTS:
        if bad in doc:
            problems.append(f"{rel}: still references retired host {bad}")
    if 'action="#"' in doc:
        problems.append(f"{rel}: placeholder form action")
    if "REPLACE_ME" in doc:
        problems.append(f"{rel}: REPLACE_ME placeholder left in output")

# ---------------------------------------------------------------- summary
print(f"pages checked: {len(pages)}")
for w in warnings:
    print("  warn:", w)
if problems:
    print(f"\n{len(problems)} problem(s):")
    for p in problems:
        print("  -", p)
    sys.exit(1)
print("\nNo broken internal links, anchor or meta problems found.")
