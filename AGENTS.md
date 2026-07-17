# job-status-bot

Read `SPEC.md` before doing anything — it's the source of truth for
scope, flow, and acceptance criteria. Its "Não-objetivos" section is
deliberate, not an oversight: don't implement past what's listed as
in-scope (no Notion writes, no silence detection, no Telegram button
confirmation in the MVP).

Ponytail is active (see `opencode.json`) — prefer stdlib/native/one-liners
per its ladder before reaching for a new dependency. This project has no
server and no database by design; keep it that way unless `SPEC.md`
changes first.

## Sequence for this project

Uses the global OpenCode pipeline (`~/.config/opencode/commands/`), not a
project-local one — `SPEC.md` already covers what `/spec` would normally
produce, so start at `/start`.

1. `/start job-status-bot` — investigation + `context.md` +
   `architecture.md` in `.opencode/sessions/job-status-bot/`, grounded in
   `SPEC.md`. No Linear card, no frontend — those sections in `/start`
   are dormant here.
2. `/plan job-status-bot` — phased `plan.md` from `context.md` +
   `architecture.md`.
3. `/work .opencode/sessions/job-status-bot` — implement phase by phase,
   pausing for approval between phases.
4. `/pre-pr` — runs `branch-code-reviewer`, `branch-documentation-writer`,
   `branch-test-planner` (skips `branch-master-docs-checker`, this project
   has no master docs).
