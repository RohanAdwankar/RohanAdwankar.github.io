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

Posts whose filename starts with `_` are treated as drafts and excluded from the generated site.
