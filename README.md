# Bloom & Budget

Money & adulting, minus the lecture. A static blog built for young women starting
their first job: budgeting the first salary, building savings, skipping the
expensive mistakes, and the career moves that pay for all of it.

Categories are Budgeting, Saving, Mistakes and Career. The niche is deliberately
narrow: money, saving, and work. Nothing lifestyle, home or beauty.

Live at **https://bloomandbudget.com**

---

## How this repo works

The HTML is **generated**, not hand-edited. Edit the source in `_build/`, then rebuild.

```
_build/
  config.json        site facts: domain, contact email, author + bio, audience,
                     currency, newsletter provider, analytics, niche
  posts.json         the post registry: slug, titles, meta, category, date, cover
  categories.json    category pages (name, slug, intro, SEO copy)
  components/        the ONE header, footer and newsletter box used on every page
  src/posts/*.html   article bodies (the actual writing)
  src/pages/*.html   bodies for about, legal and standalone pages
  build.py           generates every page, the sitemap and robots.txt
  make_assets.py     WebP covers + per-page social cards + placeholders
  make_pdf.py        the free printable monthly budget worksheet
  audit.py           link, anchor, heading and meta checks
```

### Rebuild after any change

```bash
python3 _build/build.py        # writes index.html, blog.html, posts/*.html, ...
python3 _build/audit.py        # exits non-zero if a link or meta tag is broken
python3 _build/make_assets.py  # only when covers change
python3 _build/make_pdf.py     # only when the worksheet changes
```

### Adding a post

1. Add an entry to `_build/posts.json` (slug, `title`, `titlePlain`, `seoTitle`
   under 60 chars, `meta` under 160, category, date, cover, excerpt).
2. Drop the article body in `_build/src/posts/<slug>.html`. Use only `p`, `h2`,
   `h3`, `ul`, `ol`, `li`, `strong`, `em`, `blockquote`, `div.callout` and
   `table.data-table`.
3. Run `build.py`. Breadcrumbs, table of contents, related posts, previous/next,
   share buttons, the author box and the newsletter box are all generated.

The footer's "latest posts" list and the homepage stats are computed from
`posts.json`, so they never go stale. Read times are counted from the real words.

---

## URLs

Clean URLs, no `.html` (`cleanUrls` in `vercel.json`), with 301s from the old
`.html` paths. `/` is the homepage. Internal links use root-absolute paths so
every page works from any depth.

## Filled-in placeholders

`_build/config.json` currently holds:

- domain `https://bloomandbudget.com`, email `hello@bloomandbudget.com`
- author Emma Jane, with a placeholder bio and a monogram photo
- audience: young women starting their first job in the United States, USD
- niche: **A** (money & adulting only; lifestyle posts filed under "Life")
- newsletter: provider `formspree`, endpoint **empty** (signup shows a fallback
  message until it is set)
- analytics: **not connected** (set `provider` to `ga4` or `plausible` and rebuild)

Change any of those in one place, rebuild, done.
