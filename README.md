# Bloom & Budget Blog

A fast, professional, static blog for the Bloom & Budget brand (money & adulting
for young women). No frameworks, no build tools — pure HTML + CSS, so it can be
hosted anywhere for free, including Vercel.

## Folder structure

```
bloom-budget-blog/
├── index.html                  ← homepage
├── about.html                  ← about + contact
├── css/
│   └── styles.css              ← entire design system
├── img/
│   ├── hero.png
│   ├── cover-budget.png
│   ├── cover-mistakes.png
│   └── cover-emergency.png
├── posts/
│   ├── budget-first-salary.html
│   ├── money-mistakes.html
│   └── emergency-fund.html
└── README.md
```

## Deploy to Vercel (free, ~10 minutes)

### Step 1 — Put the files on GitHub
1. Create a free account at github.com (if you don't have one).
2. Click **New repository**, name it `bloom-budget-blog`, set it to **Public**, click **Create**.
3. On the repo page click **“uploading an existing file”**.
4. Drag in ALL the files/folders from this zip (index.html, about.html, the css/
   img/ posts/ folders) — not the zip itself.
5. Click **Commit changes**.

### Step 2 — Deploy on Vercel
1. Create a free account at vercel.com — sign up **with GitHub**.
2. Click **Add New → Project**.
3. Find `bloom-budget-blog` in the list and click **Import**.
4. Leave every setting as-is and click **Deploy**.
5. In ~30 seconds you get a live URL like `bloom-budget-blog.vercel.app`.

### Step 3 — Custom domain (optional)
In Vercel: Project → Settings → Domains → add `bloomandbudget.com` (or any
domain you buy) and follow the DNS instructions shown.

## Before you launch — replace these placeholders
- `https://payhip.com/your-store` (appears in nav, footers, and post CTA boxes)
  → your real Payhip store link.
- `hello@bloomandbudget.com` on about.html → your real contact email.
- Newsletter form on index.html → connect a free service (Buttondown, Beehiiv,
  or Mailchimp) and paste its form action, or keep the placeholder.

## Adding a new post later
1. Copy any file from `posts/`, rename it, and change the title, text, and image.
2. Add a card for it in the post grid in `index.html`.
3. Re-upload the changed files to GitHub — Vercel redeploys automatically.
