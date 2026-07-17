# Implementation Plan: [FEATURE]

**Branch**: `001-job-status-bot` | **Date**: 2026-07-17 | **Spec**: [./spec.md](./spec.md)

**Input**: Feature specification from `specs/001-job-status-bot/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command; its definition describes the execution workflow.

## Summary

This feature implements a serverless bot that reads a Gmail inbox, identifies emails related to job application statuses (rejection/advancement), and sends a summary notification to a Telegram chat. It uses Gmail labels as its sole state-tracking mechanism and is designed to be a simple, one-way notification system with no external database or server costs.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: `google-api-python-client`, `google-auth`, `google-generativeai`, `requests`

**Storage**: N/A (Gmail is the single source of truth for state via labels)

**Testing**: `pytest`

**Target Platform**: GitHub Actions Runner (Linux)

**Project Type**: Serverless Bot (CLI script)

**Performance Goals**: Each run must complete within the GitHub Actions `schedule` interval (e.g., 10-15 minutes).

**Constraints**: Must operate within the free-tier limits of the Gmail and Gemini APIs. Must not require any persistent storage or running servers.

**Scale/Scope**: MVP is scoped to a single user's Gmail account and a single Telegram chat.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

*   [x] **Serverless & Cost-Free**: Does the architecture rely exclusively on GitHub Actions or other serverless, zero-cost infrastructure?
*   [x] **Gmail as SoT**: Does the solution use Gmail as the single source of truth for state, with no external databases?
*   [x] **Unidirectional Flow**: Is the data flow one-way (read -> notify) without writing back to external services like Notion?
*   [x] **Minimal Permissions**: Does the implementation use the narrowest possible, read-only permissions required?
*   [x] **Simplicity (Ponytail)**: Is this the simplest possible solution? Have all non-essential dependencies and abstractions been avoided?

## Project Structure

### Documentation (this feature)

```text
specs/001-job-status-bot/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── gemini-schema.json
│   └── telegram-api.md
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
# Single project structure
src/
├── bot/
│   ├── __init__.py
│   ├── gmail_client.py
│   ├── llm_handler.py
│   ├── notifier.py
│   └── main.py
├── config/
│   └── ats_domains.txt
└── utils/
    └── auth.py

tests/
├── integration/
│   └── test_main_flow.py
└── unit/
    ├── test_gmail_client.py
    ├── test_llm_handler.py
    └── test_notifier.py
```

**Structure Decision**: A simple, single-project structure is sufficient for this bot. The core logic is separated into modules for interacting with external services (Gmail, LLM, Telegram), with a main entry point to orchestrate the flow. Configuration is externalized.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A       | -          | -                                   |

