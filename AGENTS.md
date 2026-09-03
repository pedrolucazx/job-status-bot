# job-status-bot

Read `SPEC.md` before doing anything — it's the source of truth for
scope, flow, and acceptance criteria. Its "Não-objetivos" section is
deliberate, not an oversight: don't implement past what's listed as
in-scope (no Notion writes, no silence detection, no Telegram button
confirmation in the MVP).

Prefer stdlib/native/one-liners before reaching for a new dependency.
This project has no server and no database by design; keep it that way
unless `SPEC.md` changes first.

## Sequence for this project

Uses the global pipeline, not a project-local one — `SPEC.md` already
covers what `/spec` would normally produce, so start at `/start`. Each
command writes its own session dir; nothing of it is tracked here.

1. `/start job-status-bot` — investigation, grounded in `SPEC.md`. No
   Linear card, no frontend — those sections are dormant here.
2. `/plan job-status-bot` — phased plan.
3. `/work` — implement phase by phase, pausing for approval between them.
4. `/pre-pr` — runs `branch-code-reviewer`, `branch-documentation-writer`,
   `branch-test-planner` (skips `branch-master-docs-checker`, this project
   has no master docs).

## Deploy

Public repo, so GitHub Actions minutes are unlimited — it was private and
blew past the 2000-minute cap, since every run bills a 1-minute minimum.
If it ever goes private again, that cap comes back and the poll interval
has to drop with it.

Real triggering is external: cron-job.org calls `workflow_dispatch` every
15 min. The `schedule:` in `poll.yml` is an hourly safety net only —
GitHub's own cron has been observed 55-255 min late on this repo.
