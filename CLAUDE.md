# rav4-ntfy

Hourly RAV4 offer monitor: GitHub Actions (`.github/workflows/watch.yml`) runs `carwatch`, sends
ntfy pushes, and commits `state.json`. README (Polish) has setup and criteria; criteria live in
`carwatch/config.py`.

## Working here
- Run locally with uv, not pip, on Python 3.12 like the workflow (newer pytest/Python combos crash):
  `uv run --python 3.12 --with-requirements requirements.txt --with pytest python -m pytest -q`.
  Run `carwatch.main` with a real `NTFY_TOPIC` only if Tomasz asks: it sends real notifications.
- The default branch is `master`. The workflow commits `state.json` to it every hour, so the remote is
  usually ahead: `git pull --rebase` before committing, then `git push origin master`. Never hand-edit `state.json`.
- PUBLIC repo: no secrets, tokens or the ntfy topic in code, commits or logs. They are Actions secrets.
- Actions are free here only because the repo is public; don't make it private.

## Long-term memory
@~/personal-bootstrap/memory/projects/rav4-ntfy.md
