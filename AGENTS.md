## Agent skills

### Issue tracker

Issues are tracked as local markdown files under `.scratch/<feature-slug>/`. See `docs/agents/issue-tracker.md`.

### Triage labels

This repo uses the default five-role triage vocabulary. See `docs/agents/triage-labels.md`.

### Domain docs

This repo uses root `CONTEXT.md` as the current domain context, with supporting background under `docs/context/`. See `docs/agents/domain.md`.

### Local Python workflow

Use UV as the canonical local Python workflow. Run tests with `uv run python -m unittest discover -s tests` from the repo root.
