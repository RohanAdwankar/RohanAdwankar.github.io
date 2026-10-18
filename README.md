This is the source code for my blog https://rohanadwankar.github.io/

The repo itself contains both the build information as well as the posts and drafts.

Posts whose filename starts with `_` are drafts. A draft is still built and deployed at `posts/<name>.html` (without the underscore), so it can be previewed and shared by link, but it is not listed on the homepage. Rename the file without the underscore to list it.

Files under `static/` are copied into `dist/` as they are. 

HTML is generated from Markdown by `scripts/build.py` into `dist/`.

Local build:

```bash
uv run python scripts/build.py
```

Tests (they build the site and check that draft posts stay off the homepage while still being published):

```bash
uv run python -m unittest discover -s tests -v
```

They run in CI on every pull request and before every deploy.

Deployment:

```bash
git push origin main
```

The GitHub Actions workflow at `.github/workflows/deploy.yml` rebuilds the site and deploys it to GitHub Pages on push.
