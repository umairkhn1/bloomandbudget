#!/usr/bin/env python3
"""
Bloom & Budget — static site builder.

Single source of truth:
  _build/config.json      site facts (domain, author, newsletter, analytics)
  _build/posts.json       post registry (slug, title, meta, category, date, cover)
  _build/categories.json  category pages
  _build/src/posts/*.html article bodies (the writing)
  _build/src/pages/*.html bodies for standalone pages
  _build/components/*.html  shared header + footer, used by every page

Output: real .html files at the repo root and in posts/.
Run:    python3 _build/build.py
"""

import json
import os
import re
import html
import html as html_lib
import math
import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "_build"
SRC = BUILD / "src"
COMP = BUILD / "components"

CFG = json.loads((BUILD / "config.json").read_text())
POSTS = sorted(json.loads((BUILD / "posts.json").read_text()),
               key=lambda p: p["date"], reverse=True)
CATS = json.loads((BUILD / "categories.json").read_text())

SITE = CFG["site"]
AUTHOR = CFG["author"]
DOMAIN = SITE["domain"].rstrip("/")
EMAIL = SITE["contactEmail"]
BRAND = SITE["name"]
TODAY = datetime.date.today().isoformat()
CSS_VERSION = "11"

WRITTEN = []


# ---------------------------------------------------------------- utilities

def esc(text):
    return html.escape(text, quote=True)


def slugify(text):
    text = re.sub(r"<[^>]+>", "", str(text))
    text = html.unescape(text).lower()
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text or "section"


def words_in(body):
    return len(re.sub(r"<[^>]+>", " ", body).split())


def read_time(body):
    return max(1, int(round(words_in(body) / 225.0)))


def fmt_date(iso, style="long"):
    d = datetime.date.fromisoformat(iso)
    if style == "long":
        return f"{d.strftime('%B')} {d.day}, {d.year}"
    return iso


def write(rel_path, content):
    path = ROOT / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    WRITTEN.append(str(rel_path))


def fill(template, tokens):
    out = template
    for key, value in tokens.items():
        out = out.replace("{{%s}}" % key, str(value))
    return out


# ---------------------------------------------------------------- components

HEADER_TMPL = (COMP / "header.html").read_text()
FOOTER_TMPL = (COMP / "footer.html").read_text()
NEWSLETTER_TMPL = (COMP / "newsletter.html").read_text()
NEWSLETTER_SOON_TMPL = (COMP / "newsletter-soon.html").read_text()

NAV_KEYS = {"home": "HOME", "blog": "BLOG", "about": "ABOUT",
            "free-budget-template": "TEMPLATE"}


def header(active="home"):
    tokens = {v: "" for v in NAV_KEYS.values()}
    if active in NAV_KEYS:
        tokens[NAV_KEYS[active]] = ' class="active" aria-current="page"'
    return fill(HEADER_TMPL, tokens)


def footer():
    latest = "\n".join(
        f'            <li><a href="/posts/{p["slug"]}">{esc(p["titlePlain"])}</a></li>'
        for p in POSTS[:4]
    )
    category_links = "\n".join(
        f'            <li><a href="/{c["slug"]}">{esc(c["name"])}</a></li>'
        for c in CATS
    )
    site_links = "\n".join([
        '            <li><a href="/blog">All posts</a></li>',
        '            <li><a href="/free-budget-template">Free budget template</a></li>',
        '            <li><a href="/about">About</a></li>',
        f'            <li><a href="mailto:{EMAIL}">Contact</a></li>',
    ])
    return fill(FOOTER_TMPL, {
        "LATEST_POSTS": latest,
        "CATEGORY_LINKS": category_links,
        "SITE_LINKS": site_links,
        "TAGLINE_LONG": esc(f"{SITE['tagline']}. Built for first salaries, first "
                            "paychecks, and the money decisions that come "
                            "with them."),
        "EMAIL": EMAIL,
        "YEAR": str(datetime.date.today().year),
    })


_newsletter_counter = [0]


def newsletter(variant="section", subject="Money Bloom"):
    _newsletter_counter[0] += 1
    uid = f"nl-email-{_newsletter_counter[0]}"
    n = SITE["newsletter"]
    provider = n.get("provider") or ""
    endpoint = n.get("endpoint") or ""
    if not endpoint:
        return fill(NEWSLETTER_SOON_TMPL, {"VARIANT": variant, "EMAIL": EMAIL})
    return fill(NEWSLETTER_TMPL, {
        "UID": uid,
        "VARIANT": variant,
        "PROVIDER": esc(provider),
        "ENDPOINT": esc(endpoint),
        "MAILCHIMP_USER": esc(n.get("mailchimpUser") or ""),
        "MAILCHIMP_LIST": esc(n.get("mailchimpListId") or ""),
        "BUTTONDOWN_USER": esc(n.get("buttondownUser") or ""),
        "EMAIL": EMAIL,
    })


# ---------------------------------------------------------------- head

def analytics_snippet():
    a = SITE["analytics"]
    provider = a.get("provider")
    if provider == "ga4" and a.get("ga4MeasurementId"):
        gid = a["ga4MeasurementId"]
        return (f'  <script async src="https://www.googletagmanager.com/gtag/js?id={gid}"></script>\n'
                "  <script>\n"
                "    window.dataLayer = window.dataLayer || [];\n"
                "    function gtag(){dataLayer.push(arguments);}\n"
                f"    gtag('js', new Date());\n    gtag('config', '{gid}');\n"
                "  </script>\n")
    if provider == "plausible" and a.get("plausibleDomain"):
        d = a["plausibleDomain"]
        return (f'  <script defer data-domain="{d}" '
                'src="https://plausible.io/js/script.js"></script>\n')
    return ("  <!-- Analytics: not connected yet. Set site.analytics.provider in "
            "_build/config.json to \"ga4\" or \"plausible\", rebuild, and the tag "
            "appears here on every page. -->\n")


def head(title, desc, path, og_image, page_type="website", jsonld=None,
         extra_head=""):
    canonical = DOMAIN + path
    og_url = DOMAIN + og_image
    blocks = [
        "<!DOCTYPE html>",
        '<html lang="en">',
        "<head>",
        '  <meta charset="UTF-8">',
        '  <script async src="https://pagead2.googlesyndication.com/pagead/js/'
        'adsbygoogle.js?client=%s" crossorigin="anonymous"></script>' % SITE["adsenseClient"],
        '  <meta name="viewport" content="width=device-width, initial-scale=1">',
        f"  <title>{esc(title)}</title>",
        f'  <meta name="description" content="{esc(desc)}">',
        f'  <link rel="canonical" href="{canonical}">',
        (f'  <meta name="msvalidate.01" content="{bing_token}">'
         if (bing_token := SITE.get("verification", {}).get("bing")) else None),
        (f'  <meta name="p:domain_verify" content="{pin_token}">'
         if (pin_token := (os.environ.get("PINTEREST_DOMAIN_VERIFICATION_TOKEN")
                           or SITE.get("verification", {}).get("pinterest"))) else None),
        f'  <meta name="theme-color" content="#faf6f0">',
        f'  <meta property="og:site_name" content="{esc(BRAND)}">',
        f'  <meta property="og:type" content="{page_type}">',
        f'  <meta property="og:url" content="{canonical}">',
        f'  <meta property="og:title" content="{esc(title)}">',
        f'  <meta property="og:description" content="{esc(desc)}">',
        f'  <meta property="og:image" content="{og_url}">',
        '  <meta property="og:image:width" content="1200">',
        '  <meta property="og:image:height" content="630">',
        f'  <meta property="og:image:alt" content="{esc(title)}">',
        '  <meta name="twitter:card" content="summary_large_image">',
        f'  <meta name="twitter:title" content="{esc(title)}">',
        f'  <meta name="twitter:description" content="{esc(desc)}">',
        f'  <meta name="twitter:image" content="{og_url}">',
        '  <link rel="preconnect" href="https://fonts.googleapis.com">',
        '  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>',
        '  <link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,'
        'wght@0,500;0,600;0,700;1,500&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">',
        f'  <link rel="stylesheet" href="/css/styles.css?v={CSS_VERSION}">',
        '  <link rel="icon" href="/img/favicon/v2/favicon.ico" sizes="any">',
        '  <link rel="icon" href="/img/favicon/v2/favicon-32.png" sizes="32x32" type="image/png">',
        '  <link rel="icon" href="/img/favicon/v2/favicon-96.png" sizes="96x96" type="image/png">',
        '  <link rel="icon" href="/img/favicon/v2/favicon-192.png" sizes="192x192" type="image/png">',
        '  <link rel="apple-touch-icon" href="/img/favicon/v2/apple-touch-icon.png">',
        '  <meta name="google-adsense-account" content="%s">' % SITE["adsenseClient"],
        '  <meta name="robots" content="index,follow">',
        analytics_snippet().rstrip("\n"),
        extra_head.rstrip("\n"),
        jsonld or "",
        "</head>",
    ]
    return "\n".join(b for b in blocks if b is not None)


def jsonld_script(obj):
    return ('  <script type="application/ld+json">\n'
            + json.dumps(obj, indent=2, ensure_ascii=False)
            + "\n  </script>\n")



def extract_faq(body_html):
    """Q/A pairs from the post's FAQ section, as plain text for FAQPage schema."""
    m = re.search(r"<h2[^>]*>FAQ[^<]*</h2>", body_html)
    if not m:
        return []
    rest = body_html[m.end():]
    # the FAQ ends at the next heading, the next section or the next component block
    stop = re.search(r"<h2|<section|<div|<aside|<footer", rest)
    chunk = rest[:stop.start()] if stop else rest
    out = []
    parts = re.split(r"<h3[^>]*>", chunk)[1:]
    for part in parts:
        q_html, _, after = part.partition("</h3>")
        question = html_lib.unescape(re.sub(r"<[^>]+>", "", q_html)).strip()
        answer = " ".join(
            html_lib.unescape(re.sub(r"<[^>]+>", "", pa)).strip()
            for pa in re.findall(r"<p[^>]*>(.*?)</p>", after, re.S))
        answer = re.sub(r"\s+", " ", answer).strip()
        if question.endswith("?") and answer:
            out.append((question, answer))
    return out


def faq_node(pairs, url):
    return {
        "@type": "FAQPage",
        "@id": url + "#faq",
        "url": url,
        "mainEntity": [
            {"@type": "Question",
             "name": q,
             "acceptedAnswer": {"@type": "Answer", "text": a}}
            for q, a in pairs],
    }


def person_node():
    return {
        "@type": "Person",
        "name": AUTHOR["name"],
        "url": DOMAIN + "/about",
        "jobTitle": AUTHOR["role"],
    }


ORG_NODE = {
    "@type": "Organization",
    "name": "Bloom & Budget",
    "url": DOMAIN + "/",
    "logo": {
        "@type": "ImageObject",
        "url": DOMAIN + "/img/brand/peony-badge-512.png",
        "width": 512,
        "height": 512,
    },
    "description": SITE["description"],
    "sameAs": ["https://www.pinterest.com/bloomandbudget1/"],
    "email": SITE["contactEmail"],
}


# ---------------------------------------------------------------- post helpers

def post_cover_img(post, sizes="(max-width: 620px) 100vw, 33vw", cls="", lazy=True):
    attrs = [f'src="{post["cover"]}"',
             f'alt="{esc(post["coverAlt"])}"',
             f'width="{post.get("coverWidth", 1200)}"',
             f'height="{post.get("coverHeight", 750)}"']
    if cls:
        attrs.append(f'class="{cls}"')
    if lazy:
        attrs.append('loading="lazy"')
        attrs.append('decoding="async"')
    else:
        attrs.append('loading="eager"')
        attrs.append('fetchpriority="high"')
    return "<img " + " ".join(attrs) + ">"


def post_card(post):
    return f"""          <article class="post-card">
            <a href="/posts/{post['slug']}" class="thumb" aria-hidden="true" tabindex="-1">
              {post_cover_img(post)}
            </a>
            <div class="body">
              <span class="tag">{esc(post['tag'])}</span>
              <h3><a href="/posts/{post['slug']}">{esc(post['titlePlain'])}</a></h3>
              <p class="excerpt">{esc(post['excerpt'])}</p>
              <div class="meta"><span>{fmt_date(post['date'])}</span><span>{post['_read']} min read</span>{f"<span>Updated {fmt_date(post['updated'])}</span>" if post.get('updated') else ""}</div>
            </div>
          </article>"""


def post_grid(posts):
    return "\n".join(post_card(p) for p in posts)


def grid_class(posts):
    """Column count that keeps the last row full: 1 wide card, 2x2, or 3 across."""
    n = len(posts)
    if n == 1:
        return "post-grid post-grid--single"
    if n == 2:
        return "post-grid post-grid--two"
    if n % 3 == 1 and n % 2 == 0:
        return "post-grid post-grid--two"
    return "post-grid"


def share_bar(title, url):
    wa = "https://wa.me/?text=" + esc(f"{title} {url}")
    x = ("https://twitter.com/intent/tweet?text=" + esc(title)
         + "&url=" + esc(url))
    return f"""      <div class="share-bar" data-share-url="{esc(url)}" data-share-title="{esc(title)}">
        <span class="share-label">Share this post</span>
        <div class="share-buttons">
          <a class="share-btn share-wa" href="{wa}" target="_blank" rel="noopener">WhatsApp</a>
          <a class="share-btn share-x" href="{x}" target="_blank" rel="noopener">X</a>
          <button type="button" class="share-btn share-copy" data-copy-link>Copy link</button>
        </div>
      </div>"""


def heading_ids(body):
    """Give every h2 an id and return (body, [(id, text), ...])."""
    toc = []
    used = set()

    def repl(match):
        attrs, text = match.group(1), match.group(2)
        if "id=" in attrs:
            return match.group(0)
        base = slugify(text)
        slug, i = base, 2
        while slug in used:
            slug = f"{base}-{i}"
            i += 1
        used.add(slug)
        toc.append((slug, text))
        return f'<h2{attrs} id="{slug}">{text}</h2>'

    return re.sub(r"<h2([^>]*)>(.*?)</h2>", repl, body, flags=re.S), toc


def table_of_contents(toc):
    if len(toc) < 3:
        return ""
    items = "\n".join(
        f'          <li><a href="#{slug}">{text}</a></li>' for slug, text in toc
    )
    return f"""      <nav class="toc" aria-labelledby="toc-title">
        <p class="toc-title" id="toc-title">In this post</p>
        <ol>
{items}
        </ol>
      </nav>
"""


def clean_body(body):
    body = re.sub(r'\sstyle="[^"]*"', "", body)
    body = body.replace("<br>", "<br>")
    return body.strip()


def page_tokens():
    money = [p for p in POSTS if p["money"]]
    return {
        "MONEY_POST_LINKS": "\n".join(
            f'        <li><a href="/posts/{p["slug"]}">{esc(p["titlePlain"])}</a></li>'
            for p in money),
        "POST_COUNT": len(POSTS),
        "AVG_READ": int(round(sum(p["_read"] for p in POSTS) / len(POSTS))),
        "EMAIL": EMAIL,
        "DOMAIN": DOMAIN,
        "DOMAIN_HOST": SITE["domainHost"],
        "AUTHOR_NAME": AUTHOR["name"],
        "AUTHOR_BIO": esc(AUTHOR["bio"]),
        "NEWSLETTER": newsletter("section"),
    }


# ---------------------------------------------------------------- pages

def page_shell(meta, main_html, active="", extra_head="", body_class=""):
    return "\n".join([
        head(meta["title"], meta["desc"], meta["path"], meta["og"],
             meta.get("type", "website"), meta.get("jsonld"), extra_head),
        f'<body{" class=" + chr(34) + body_class + chr(34) if body_class else ""}>',
        '  <a class="skip-link" href="#main">Skip to content</a>',
        "",
        header(active),
        "",
        '  <main id="main">',
        main_html,
        "  </main>",
        "",
        footer(),
        "",
        '  <script src="/js/site.js?v=8" defer></script>',
        "</body>",
        "</html>",
        "",
    ])


def build_post(post):
    body = clean_body((SRC / "posts" / f"{post['slug']}.html").read_text())
    body, toc = heading_ids(body)
    words = words_in(body)
    post["_read"] = max(1, int(round(words / 225.0)))
    post["_words"] = words

    url = f"{DOMAIN}/posts/{post['slug']}"
    category = next((c for c in CATS if c["slug"] == post["categorySlug"]), None)

    if post.get("templateCallout"):
        body += """

      <div class="product-box">
        <span class="eyebrow">Free download</span>
        <h3>Want this as a printable page?</h3>
        <p>Grab the free one-page monthly budget template. Print it, fill it in with a pen, done in ten minutes.</p>
        <a class="btn btn-primary" href="/free-budget-template">Get the free budget template</a>
      </div>"""

    disclaimer = ""
    if post.get("money"):
        disclaimer = ('        <p class="post-disclaimer">Educational content only, not '
                      'financial advice. Read the <a href="/disclaimer">full disclaimer</a>.</p>')

    # related: same category, then the same shelf (money vs life), then the rest
    current = post["slug"]
    same = [p for p in POSTS if p["slug"] != current
            and p["categorySlug"] == post["categorySlug"]]
    cluster = [p for p in POSTS if p["slug"] != current and p not in same
               and p["money"] == post["money"]]
    rest = [p for p in POSTS if p["slug"] != current
            and p not in same and p not in cluster]
    related = (same + cluster + rest)[:3]
    same_cat = related and all(
        r["categorySlug"] == post["categorySlug"] for r in related)
    related_heading = (f"More from {post['category']}" if same_cat
                       else "Keep reading")

    ordered = sorted(POSTS, key=lambda p: p["date"])
    idx = [p["slug"] for p in ordered].index(post["slug"])
    older = ordered[idx - 1] if idx > 0 else None
    newer = ordered[idx + 1] if idx < len(ordered) - 1 else None

    nav_parts = []
    if older:
        nav_parts.append(
            f'        <a class="post-nav-item prev" href="/posts/{older["slug"]}">'
            f'<span>Previous post</span><strong>{esc(older["titlePlain"])}</strong></a>')
    else:
        nav_parts.append('        <span></span>')
    if newer:
        nav_parts.append(
            f'        <a class="post-nav-item next" href="/posts/{newer["slug"]}">'
            f'<span>Next post</span><strong>{esc(newer["titlePlain"])}</strong></a>')
    post_nav = ('      <nav class="post-nav" aria-label="More posts">\n'
                + "\n".join(nav_parts) + "\n      </nav>")

    faq_pairs = extract_faq(body)
    article_jsonld = jsonld_script({
        "@context": "https://schema.org",
        "@graph": [
            person_node(),
            {
                "@type": "BlogPosting",
                "headline": post["titlePlain"],
                "description": post["meta"],
                "image": DOMAIN + f"/img/og/{post['slug']}.jpg",
                "datePublished": post["date"],
                "dateModified": TODAY,
                "wordCount": words,
                "articleSection": post["category"],
                "inLanguage": "en-US",
                "author": {"@type": "Person", "name": AUTHOR["name"],
                           "url": DOMAIN + "/about"},
                "publisher": ORG_NODE,
                "mainEntityOfPage": {"@type": "WebPage", "@id": url},
                "url": url,
            },
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Home",
                     "item": DOMAIN + "/"},
                    {"@type": "ListItem", "position": 2,
                     "name": post["category"],
                     "item": f"{DOMAIN}/{post['categorySlug']}"},
                    {"@type": "ListItem", "position": 3,
                     "name": post["titlePlain"], "item": url},
                ],
            },
        ],
    })
    if faq_pairs:
        article_jsonld += jsonld_script(
            {"@context": "https://schema.org", **faq_node(faq_pairs, url)})

    answer = post.get("shortAnswer", "")
    if answer:
        intro_end = re.search(r"\n\s*<h2", body)
        block = ('\n      <p class="short-answer"><strong>Short answer:</strong> '
                 + answer + "</p>\n")
        if intro_end:
            body = body[:intro_end.start()] + block + body[intro_end.start():]
        else:
            body = body + block

    main = f"""    <section class="article-hero">
      <div class="container">
        <nav class="breadcrumbs" aria-label="Breadcrumb">
          <ol>
            <li><a href="/">Home</a></li>
            <li><a href="/{post['categorySlug']}">{esc(post['category'])}</a></li>
            <li aria-current="page">{esc(post['titlePlain'])}</li>
          </ol>
        </nav>
        <span class="tag">{esc(post['tag'])}</span>
        <h1>{post['title']}</h1>
        <div class="meta">
          <span>{fmt_date(post['date'])}</span><span>·</span>
          <span>{post['_read']} min read</span><span>·</span>
          <span>by <a href="/about" rel="author">{esc(AUTHOR['name'])}</a></span>
          {f"<span>·</span><span>Updated {fmt_date(post['updated'])}</span>" if post.get('updated') else ""}
        </div>
{disclaimer}
      </div>
    </section>

    <div class="article-cover">
      {post_cover_img(post, sizes="(max-width: 900px) 100vw, 880px", lazy=False)}
    </div>

    <article class="prose">
{table_of_contents(toc)}
{body}

{share_bar(post['titlePlain'], url)}

      <p class="back-to-blog"><a href="/blog">&larr; Back to all posts</a></p>
    </article>

    <aside class="author-box" aria-label="About the author">
      <img src="{AUTHOR['photo']}" alt="{esc(AUTHOR['photoAlt'])}" width="120" height="120" loading="lazy" decoding="async">
      <div>
        <p class="author-label">Written by</p>
        <h2 class="author-name"><a href="/about">{esc(AUTHOR['name'])}</a></h2>
        <p>{esc(AUTHOR['bio'])}</p>
      </div>
    </aside>

    <section class="section related-section">
      <div class="container">
        <div class="section-head">
          <div>
            <span class="eyebrow">Keep reading</span>
            <h2>{esc(related_heading)}</h2>
          </div>
          <p><a href="/blog">See all posts</a></p>
        </div>
        <div class="post-grid">
{post_grid(related)}
        </div>
      </div>
    </section>

{post_nav}

    <section class="section post-newsletter">
      <div class="container">
{newsletter('post')}
      </div>
    </section>"""

    meta = {
        "title": post["seoTitle"],
        "desc": post["meta"],
        "path": f"/posts/{post['slug']}",
        "og": f"/img/og/{post['slug']}.jpg",
        "type": "article",
        "jsonld": article_jsonld,
    }
    write(f"posts/{post['slug']}.html",
          page_shell(meta, main, active="blog"))


def build_index():
    money_cats = {"budgeting", "saving", "mistakes"}
    money = [p for p in POSTS if p["categorySlug"] in money_cats]
    career = [p for p in POSTS if p["categorySlug"] not in money_cats]
    avg_read = int(round(sum(p["_read"] for p in POSTS) / len(POSTS)))
    total_posts = len(POSTS)

    latest_list = "\n".join(
        f'            <li><a href="/posts/{p["slug"]}">{esc(p["titlePlain"])}</a></li>'
        for p in POSTS[:4])

    hero_img = ('<img src="/img/hero.webp" alt="Warm minimal desk scene with notebook, '
                'coins, coffee and a plant" width="800" height="880" '
                'loading="eager" fetchpriority="high" decoding="async">')

    career_cards = post_grid(career[:3])
    career_grid_class = grid_class(career[:3])

    main = f"""    <!-- HERO -->
    <section class="hero">
      <div class="container hero-grid">
        <div>
          <span class="eyebrow">Money &middot; Adulting &middot; No Shame</span>
          <h1>Grow your money while you <span class="accent">grow up.</span></h1>
          <p class="lead">Real talk about budgeting your first salary, dodging the mistakes everyone makes in their twenties, and building a life you don't need a vacation from. Written for young women starting their first job in the United States.</p>
          <div class="hero-actions">
            <a href="/blog" class="btn btn-primary">Read the Blog</a>
            <a href="/about" class="btn btn-outline">About B&amp;B</a>
          </div>
          <div class="hero-stats">
            <div class="stat"><b>{avg_read} min</b><span>average read</span></div>
            <div class="stat"><b>{total_posts}</b><span>posts, all free</span></div>
            <div class="stat"><b>100%</b><span>guilt-free</span></div>
          </div>
        </div>
        <div class="hero-media">
          {hero_img}
        </div>
      </div>
    </section>

    <!-- LATEST POSTS -->
    <section class="section" id="latest">
      <div class="container">
        <div class="section-head">
          <div>
            <span class="eyebrow">Fresh from the desk</span>
            <h2>The latest money posts</h2>
          </div>
          <p>Made for first salaries, first budgets, and first &ldquo;wait, is this&hellip; mine?&rdquo; moments.</p>
        </div>

        <div class="{grid_class(money[:3])}">
{post_grid(money[:3])}
        </div>
      </div>
    </section>

    <!-- QUOTE -->
    <section class="quote-strip">
      <div class="container">
        <blockquote>&ldquo;A budget is a permission slip, not a punishment.&rdquo;</blockquote>
        <cite>&mdash; the entire Bloom &amp; Budget philosophy</cite>
      </div>
    </section>

    <!-- CAREER -->
    <section class="section">
      <div class="container">
        <div class="section-head">
          <div>
            <span class="eyebrow">Beyond the budget</span>
            <h2>The career corner</h2>
          </div>
          <p>Your salary is the biggest line in your budget, so the job hunt counts. <a href="/career">All career posts &rarr;</a></p>
        </div>
        <div class="{career_grid_class}">
{career_cards}
        </div>
      </div>
    </section>

    <!-- NEWSLETTER -->
    <section class="section" id="newsletter">
      <div class="container">
{newsletter('section')}
        <p class="template-nudge">Prefer paper? <a href="/free-budget-template">Download the free printable monthly budget template</a>.</p>
      </div>
    </section>

"""

    jsonld = jsonld_script({
        "@context": "https://schema.org",
        "@graph": [
            {"@type": "WebSite", "name": BRAND, "url": DOMAIN + "/",
             "description": SITE["description"]},
            {"@type": "Blog", "name": BRAND, "url": DOMAIN + "/blog",
             "description": SITE["description"],
             "author": person_node()},
            ORG_NODE,
        ],
    })

    meta = {
        "title": "Bloom & Budget: Money & Adulting for Your First Salary",
        "desc": "A warm, no-shame blog for young women starting their first job in the US: budgeting a first salary, dodging fresh-grad money mistakes, adulting on purpose.",
        "path": "/",
        "og": "/img/og/home.jpg",
        "jsonld": jsonld,
    }
    write("index.html", page_shell(meta, main, active="home"))


def build_blog():
    chips = "\n".join(
        f'          <li><a class="chip" href="/{c["slug"]}">{esc(c["name"])}</a></li>'
        for c in CATS)
    cards = post_grid(POSTS)

    main = f"""    <section class="page-hero">
      <div class="container">
        <span class="eyebrow">The archive</span>
        <h1>Every post, newest first</h1>
        <p class="lead">{len(POSTS)} posts on budgeting, saving, the mistakes worth skipping, and the career moves that pay for all of it.</p>
      </div>
    </section>

    <section class="section blog-section">
      <div class="container">
        <div class="blog-tools">
          <label class="sr-only" for="post-search">Search posts</label>
          <input type="search" id="post-search" class="post-search" placeholder="Search posts, e.g. salary, savings, credit" autocomplete="off" data-post-search>
          <p class="search-status" role="status" aria-live="polite" data-search-status></p>
        </div>

        <ul class="chips" aria-label="Categories">
{chips}
        </ul>

        <h2 class="sr-only">All posts</h2>
        <div class="{grid_class(POSTS)}" data-post-grid>
{cards}
        </div>

        <p class="no-results" data-no-results hidden>Nothing matched that search. Try a shorter word, or <a href="/blog">clear the search</a>.</p>
      </div>
    </section>

    <section class="section">
      <div class="container">
{newsletter('section')}
      </div>
    </section>"""

    meta = {
        "title": "All Posts: The Bloom & Budget Archive",
        "desc": "Every Bloom & Budget post in one place: budgeting your first salary, building savings, money mistakes to skip, and the career moves that pay for it.",
        "path": "/blog",
        "og": "/img/og/blog.jpg",
        "jsonld": jsonld_script({
            "@context": "https://schema.org",
            "@type": "CollectionPage",
            "name": "All posts",
            "url": DOMAIN + "/blog",
            "hasPart": [
                {"@type": "BlogPosting", "headline": p["titlePlain"],
                 "url": f"{DOMAIN}/posts/{p['slug']}", "datePublished": p["date"]}
                for p in POSTS],
        }),
    }
    write("blog.html", page_shell(meta, main, active="blog"))


def build_category(cat):
    posts = [p for p in POSTS if p["categorySlug"] == cat["slug"]]
    cards = post_grid(posts) if posts else (
        '          <p class="no-results">Nothing here yet. <a href="/blog">'
        'Browse all posts</a>.</p>')

    main = f"""    <section class="page-hero">
      <div class="container">
        <nav class="breadcrumbs" aria-label="Breadcrumb">
          <ol>
            <li><a href="/">Home</a></li>
            <li><a href="/blog">Blog</a></li>
            <li aria-current="page">{esc(cat['name'])}</li>
          </ol>
        </nav>
        <span class="eyebrow">Category</span>
        <h1>{esc(cat['name'])}</h1>
        <p class="lead">{esc(cat['intro'])}</p>
        <p class="category-count">{len(posts)} post{'s' if len(posts) != 1 else ''}</p>
      </div>
    </section>

    <section class="section">
      <div class="container">
        <h2 class="sr-only">All {esc(cat['name'])} posts</h2>
        <div class="{grid_class(posts)}">
{cards}
        </div>
        <p class="back-to-blog"><a href="/blog">&larr; Back to all posts</a></p>
      </div>
    </section>

{cat.get("body", "")}"""

    meta = {
        "title": cat["seoTitle"],
        "desc": cat["meta"],
        "path": f"/{cat['slug']}",
        "og": f"/img/og/{cat['slug']}.jpg",
        "jsonld": jsonld_script({
            "@context": "https://schema.org",
            "@type": "CollectionPage",
            "name": cat["name"],
            "description": cat["intro"],
            "url": f"{DOMAIN}/{cat['slug']}",
        }),
    }
    write(f"{cat['slug']}.html", page_shell(meta, main, active="blog"))


def build_about():
    body = fill((SRC / "pages" / "about.html").read_text(), page_tokens())
    main = body
    jsonld = jsonld_script({
        "@context": "https://schema.org",
        "@graph": [
            person_node(),
            {
                "@type": "AboutPage",
                "name": "About Bloom & Budget",
                "url": DOMAIN + "/about",
                "mainEntity": person_node(),
            },
        ],
    })
    meta = {
        "title": "About Emma Jane & Bloom & Budget",
        "desc": "Who writes Bloom & Budget, why it exists, and exactly who it is for: young women starting their first job and the first salary that comes with it.",
        "path": "/about",
        "og": "/img/og/about.jpg",
        "jsonld": jsonld,
    }
    write("about.html", page_shell(meta, main, active="about"))


LEGAL_PAGES = {
    "privacy": {
        "title": "Privacy Policy: How Bloom & Budget Handles Your Data",
        "desc": "What Bloom & Budget collects, how cookies and Google AdSense work, what happens when you join the newsletter, and how to contact me about your data.",
        "h1": "Privacy Policy",
        "og": "/img/og/privacy.jpg",
    },
    "disclaimer": {
        "title": "Disclaimer: Not Financial Advice",
        "desc": "Bloom & Budget is educational content, not financial, legal or tax advice. No guarantees, no personalised recommendations, plus affiliate disclosure.",
        "h1": "Disclaimer",
        "og": "/img/og/disclaimer.jpg",
    },
    "terms": {
        "title": "Terms of Use: The Rules for Using This Site",
        "desc": "The simple terms for using Bloom & Budget: what you may share, what you may not copy, and the limits of what this site promises.",
        "h1": "Terms of Use",
        "og": "/img/og/terms.jpg",
    },
    "free-budget-template": {
        "title": "Free Budget Planner: Printable One-Page PDF (No Email)",
        "desc": "A free budget planner you print and fill in by hand. One page, no email, no app, no formulas to break. Built for a first salary and a ten-minute setup.",
        "h1": "A free budget planner you'll actually fill in",
        "og": "/img/og/free-budget-template.jpg",
    },
}


def build_legal(slug):
    cfgp = LEGAL_PAGES[slug]
    body = fill((SRC / "pages" / f"{slug}.html").read_text(), page_tokens())
    meta = {
        "title": cfgp["title"],
        "desc": cfgp["desc"],
        "path": f"/{slug}",
        "og": cfgp["og"],
    }
    faq_pairs = extract_faq(body)
    if faq_pairs:
        meta["jsonld"] = jsonld_script(
            {"@context": "https://schema.org",
             **faq_node(faq_pairs, DOMAIN + f"/{slug}")})
    write(f"{slug}.html", page_shell(meta, body))


def build_404():
    body = fill((SRC / "pages" / "404.html").read_text(), page_tokens())
    main = body
    meta = {
        "title": "Page Not Found: Bloom & Budget",
        "desc": "That page has moved or never existed. Start from the archive instead.",
        "path": "/404",
        "og": "/img/og/not-found.jpg",
    }
    page = page_shell(meta, main)
    page = page.replace('  <meta name="robots" content="index,follow">',
                        '  <meta name="robots" content="noindex,follow">')
    write("404.html", page)


def build_sitemap():
    urls = [("/", TODAY, "1.0", "weekly")]
    urls += [("/" + s, TODAY, "0.6", "monthly") for s in LEGAL_PAGES]
    urls += [("/blog", TODAY, "0.9", "weekly"), ("/about", TODAY, "0.8", "monthly")]
    urls += [(f"/{c['slug']}", TODAY, "0.7", "weekly") for c in CATS]
    urls += [(f"/posts/{p['slug']}", p.get("updated") or p["date"], "0.8", "monthly")
             for p in POSTS]
    entries = "\n".join(
        f'  <url><loc>{DOMAIN}{loc}</loc><lastmod>{mod}</lastmod>'
        f'<changefreq>{freq}</changefreq><priority>{prio}</priority></url>'
        for loc, mod, prio, freq in urls)
    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
           + entries + "\n</urlset>\n")
    write("sitemap.xml", xml)

    bots = ["Googlebot", "Bingbot", "OAI-SearchBot", "GPTBot", "ChatGPT-User",
            "PerplexityBot", "Perplexity-User", "ClaudeBot", "Claude-SearchBot",
            "Claude-User", "Applebot", "Applebot-Extended", "Google-Extended", "CCBot"]
    groups = "\n".join(f"User-agent: {b}\nAllow: /\n" for b in bots)
    robots = ("User-agent: *\nAllow: /\n\n"
              "# Search and answer engines, explicitly allowed for crawling and citation\n"
              + groups +
              f"\nSitemap: {DOMAIN}/sitemap.xml\n")
    write("robots.txt", robots)
    write("robots.txt", robots)


def build_llms():
    """llms.txt is generated, not hand-edited: new posts appear automatically."""
    topics = {
        "budget-first-salary": "The four walls, the 50/30/20 split, the three-account trick, and a fully worked $48,000 example.",
        "money-mistakes": "The ten most common and most expensive first-year money mistakes, each with a cheap fix.",
        "emergency-fund": "Why $500 comes before three months, where to keep the money, and how to fund it on a small salary.",
        "first-credit-card-build-credit": "How a FICO score is calculated, which first card to get, the four habits that build credit, and what ruins it.",
        "first-job-benefits-enrollment": "Premium, deductible, HSA, vesting and match translated, plus how to choose between two health plans and what to skip.",
        "negotiate-first-job-offer": "When to ask, what to say, which parts of an offer actually move, and what to do when the answer is no.",
        "why-it-jobs-are-hard": "What changed in tech hiring, how to spot fake job postings, and what still gets people hired.",
        "first-apartment-cost": "Deposit, first month, furnishing an empty room and the month-two bills, with a worked $1,150 apartment.",
        "first-paycheck-deductions": "Every tax and deduction between gross and net pay, why the first check is prorated, and how to read a pay stub.",
        "balcony-setup-cost": "A renter's balcony from $0 to $362, line by line, plus the lease rules and what survives weather.",
        "gaming-budget": "How to afford games without debt: the real cost of a release, when launch week is bad value, and a monthly games number.",
        "expenses-to-cut": "Ten expense cuts that cost you nothing you can feel, with typical US amounts and what each one gives up.",
        "saving-on-low-salary": "How to save when the salary is tight: why percentages fail, the $25 that survives, a $500 floor, and the four cuts worth $60 to $150 a month.",
        "50-30-20-rule": "The 50/30/20 split bucket by bucket, the same salary worked line by line, the 60/20/20 and 70/20/10 versions, and where debt payments belong.",
        "sunday-money-reset": "The 25-minute Sunday reset step by step, why weekly beats monthly, what it saves in avoided fees, and the ten-minute version for bad weeks.",
        "monthly-money-planning": "The 20-minute monthly plan in four decisions, the worked $48,000 month, the uneven four-week split, and the repair order for a month that goes wrong.",
    }
    lines = [
        f"# {SITE['name']}",
        "",
        f"> {SITE['description']} Every post is free to read, written in plain language, "
        f"priced in {SITE['currency']}, and aimed at one narrow niche: budgeting a first salary, "
        "building savings, avoiding expensive mistakes, and the career moves that pay for all of it.",
        "",
        f"Author: {AUTHOR['name']}. Contact: {SITE['contactEmail']}. "
        "Educational content only, not financial advice.",
        "",
        "## Posts",
        "",
    ]
    for p in sorted(POSTS, key=lambda x: x["date"], reverse=True):
        lines.append(f"- [{p['titlePlain']}]({DOMAIN}/posts/{p['slug']}): "
                     f"{topics.get(p['slug'], p['meta'])}")
    lines += ["", "## Pages", ""]
    for name, path, blurb in (
        ("Blog archive", "/blog", "Every post, newest first, with search and category filters."),
        ("About", "/about", f"Who writes {SITE['name']} and who it is for."),
        ("Free budget template", "/free-budget-template", "A printable monthly budget worksheet, free for personal use."),
        ("Disclaimer", "/disclaimer", "Educational content only, not financial advice."),
        ("Privacy policy", "/privacy", "What data the site collects and why."),
        ("Terms of use", "/terms", "The terms covering use of the site and its content."),
    ):
        lines.append(f"- [{name}]({DOMAIN}{path}): {blurb}")
    lines += [
        "",
        "## Notes",
        "",
        f"- Categories: {', '.join(c['name'] for c in CATS)}.",
        "- All posts include a short direct answer at the top, an FAQ with structured data, and a stated publication date.",
        f"- {SITE['name']} can be cited with attribution and a link to the post.",
        "",
    ]
    write("llms.txt", "\n".join(lines))


def compute_stats():
    """Read time for every post, before any page needs it."""
    for post in POSTS:
        body = clean_body((SRC / "posts" / f"{post['slug']}.html").read_text())
        post["_words"] = words_in(body)
        post["_read"] = max(1, int(round(post["_words"] / 225.0)))


def main():
    compute_stats()
    for post in POSTS:
        build_post(post)
    build_index()
    build_blog()
    for cat in CATS:
        build_category(cat)
    build_about()
    for slug in LEGAL_PAGES:
        build_legal(slug)
    build_404()
    build_sitemap()
    build_llms()

    avg = sum(p["_read"] for p in POSTS) / len(POSTS)
    print(f"Built {len(WRITTEN)} files.")
    for p in POSTS:
        print(f"  posts/{p['slug']}.html  {p['_words']} words  {p['_read']} min")
    print(f"Average read: {avg:.2f} min -> {int(round(avg))} min")


if __name__ == "__main__":
    main()
