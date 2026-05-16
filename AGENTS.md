## Agent skills

### Issue tracker

Issues are tracked as local markdown files under `.scratch/<feature-slug>/`. See `docs/agents/issue-tracker.md`.

### Triage labels

This repo uses the default five-role triage vocabulary. See `docs/agents/triage-labels.md`.

### Domain docs

This repo uses a single-context domain-doc layout, with current context material under `docs/context/`. See `docs/agents/domain.md`.

### Local Python workflow

Use UV as the canonical local Python workflow. Run tests with `uv run python -m unittest discover -s tests` from the repo root.
