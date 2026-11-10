# SeekMakeup.com — coming-soon page

A static coming-soon page for SeekMakeup, a directory of stores and the makeup brands they carry. It launches first in New York City.

- `public/`: the site (index.html, thanks.html)
- `functions/api/subscribe.js`: saves email signups to the Cloudflare KV namespace `seekmakeup-signups` (binding `SIGNUPS`)
- `wrangler.toml`: Cloudflare Pages settings

## Deploy on Cloudflare Pages
In the Cloudflare dashboard, go to Workers & Pages → Create → Pages → Connect to Git and pick this repo. Leave the framework preset at None, leave the build command empty, and set the output directory to `public`.

Created by Claude
