<!-- Title format examples:
       add: NewRelay (mixed)
       fix: SomeRelay — price update
       status: GPTGOD → inactive
       feat: add UiUiAPI fetcher
-->
<!--
  AI agents: follow docs/agent-contribute.md before opening this PR.
  Edit data/providers.yaml only. Never hand-edit README tables.
  Run: python -m scripts.validate
-->

## What this changes

<!-- One line. -->

## Checklist

- [ ] Edited `data/providers.yaml` only (not the README tables — they auto-regenerate; CI rejects hand-edits)
- [ ] Followed [`data/schema.md`](../data/schema.md)
- [ ] `status: unverified` if I cannot independently verify (self-submissions **must** use this)
- [ ] Self-submission: `risk_flags: [operator_submitted]`
- [ ] Plain `https://` URL only — no `utm_*` / `ref=` / affiliate params
- [ ] No marketing copy / superlatives in `notes` (one factual sentence, ≤ 360 chars)
- [ ] Claims have a dated source where non-obvious
- [ ] If adding a price fetcher: created `fetchers/<id>.py`, registered in `fetchers/__init__.REGISTRY`, added aliases to `data/canonical-models.yaml`

## Source / verification

<!-- How did you verify? Link or short description. -->

## Are you the operator of this station? (Optional)

<!-- Self-submissions are welcome. Disclose for transparency; it doesn't change acceptance. -->

---

> **Schema CI ([pr-validate.yml](../.github/workflows/pr-validate.yml)) runs on every change to `data/`, `fetchers/`, `scripts/`, or `pyproject.toml`.**
> If you see a red ✗, scroll to the action log — it usually points to the exact field. Fix and push; CI re-runs automatically.
