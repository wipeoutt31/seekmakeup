# SeekMakeup.com — coming-soon page

A static coming-soon page for SeekMakeup, a directory of stores and the makeup brands they carry. It launches first in New York City.

- `public/`: the site (index.html, thanks.html)
- `functions/api/subscribe.js`: saves email signups to the Cloudflare KV namespace `seekmakeup-signups` (binding `SIGNUPS`)
- `wrangler.toml`: Cloudflare Pages settings

## Deploy on Cloudflare Pages
In the Cloudflare dashboard, go to Workers & Pages → Create → Pages → Connect to Git and pick this repo. Leave the framework preset at None, leave the build command empty, and set the output directory to `public`.

Created by Claude

## Directory pages (added Nov 10, 2026)

The brand, store and category pages are generated, not hand-written.

1. Export the "SeekMakeup – Data" Google Sheet tabs (Brands, Stores, Chain carries, Carries) into `data/sheet.json`.
2. Run `python3 scripts/build.py`. It rewrites `public/index.html`, `public/brands/`, `public/stores/`, `public/makeup/`, `public/assets/` and `public/sitemap.xml`.
3. Commit and push to `main`; Cloudflare Pages publishes it.

Rules the build follows:
- Chain stores get their brands from the chain's column on the Chain carries tab. CVS, Walgreens/Duane Reade, Target and Ulta show "Selection varies".
- The Carries tab adds store-specific brands (brand stores, exceptions).
- Only the part of a store's Notes after "Show on site:" is shown publicly.
- Edit `scripts/site.css` and `scripts/finder.js`, not the copies in `public/assets/`.
