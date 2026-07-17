<!--
---
sync_impact_report:
  version_change: "0.0.0 → 1.0.0"
  modified_principles: []
  added_sections:
    - "Core Principles"
    - "Development Workflow"
    - "Governance"
  removed_sections: []
  updated_templates:
    - path: ".specify/templates/plan-template.md"
      status: "pending"
    - path: ".specify/templates/spec-template.md"
      status: "pending"
    - path: ".specify/templates/tasks-template.md"
      status: "pending"
  deferred_todos: []
---
-->
# job-status-bot Constitution

## Core Principles

### I. Serverless & Cost-Free Execution
The bot must operate without dedicated servers, relying on scheduled GitHub Actions to maintain zero operational cost. This is a non-negotiable architectural constraint defined in the project's core specification.

### II. Gmail as the Single Source of Truth
All state is managed within Gmail through labels (`jobbot-processado`). No external databases, flat files, or other state stores are permitted in the MVP. This simplifies the architecture and avoids data synchronization issues.

### III. Unidirectional, Notification-Only Workflow
The bot's role is strictly to read emails and send notifications to a pre-configured Telegram chat. It must not write data back to any external service (e.g., Notion), modify emails (beyond applying a process label), or support user interactions beyond the initial notification. This enforces a simple, one-way data flow.

### IV. Minimal, Read-Only Permissions
The bot must request the narrowest possible OAuth scope required for its operation (`gmail.modify` is needed only for applying labels). It must never delete, archive, or mark emails as read. The user's inbox integrity is paramount.

### V. Simplicity and Standard Tooling (Ponytail Principle)
Solutions must be the simplest that can possibly work. Prefer Python's standard library and well-established, minimal dependencies (`google-api-python-client`, `requests`) over adding new ones. Avoid speculative features and over-engineering, as enforced by the active Ponytail agent configuration.

## Development Workflow

All development must adhere to the sequence defined in `AGENTS.md`. The `SPEC.md` is the source of truth for scope and acceptance criteria. No features or changes shall be implemented that are listed in the "Não-objetivos" section of the specification.

## Governance

This Constitution is the definitive source of truth for project principles and architecture. All code, PRs, and reviews must verify compliance with these rules. Any proposed deviation must be justified and result in a formal amendment to this document.

**Version**: 1.0.0 | **Ratified**: 2026-07-17 | **Last Amended**: 2026-07-17
