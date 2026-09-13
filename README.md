HTML is generated from Markdown by `scripts/build.py` into `dist/`.

Local build:

```bash
uv run python scripts/build.py
```

Deployment:

```bash
git push origin main
```

The GitHub Actions workflow at `.github/workflows/deploy.yml` rebuilds the site and deploys it to GitHub Pages on push.

Posts whose filename starts with `_` are drafts. A draft is still built and deployed at `posts/<name>.html` (without the underscore), so it can be previewed and shared by link, but it is not listed on the homepage. Rename the file without the underscore to list it.

Files under `static/` are copied into `dist/` as they are. `static/js/semfont/` is a copy of the [semfont](https://github.com/RohanAdwankar/semfont) engine, which the semfont post runs in the browser.
