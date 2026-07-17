# Data Model: Job Status Bot

**Date**: 2026-07-17

**Prerequisite**: [research.md](./research.md)

## Objective

This document defines the key data structures for the Job Status Bot. As the bot is stateless and uses Gmail as its source of truth, this model describes the transient data structures used during a single run of the bot's logic.

---

## 1. `JobApplicationEmail`

Represents an email retrieved from Gmail for processing.

- **Source**: Gmail API (`users.messages.get`)
- **Description**: The primary input for the bot's workflow.

| Field       | Type   | Description                                            | Example                                   |
|-------------|--------|--------------------------------------------------------|-------------------------------------------|
| `id`        | string | The unique ID of the message in Gmail.                 | `"18f8c4b3d3f4a2b1"`                      |
| `sender`    | string | The `From` header of the email.                        | `"Gupy <noreply@gupy.io>"`                |
| `subject`   | string | The subject line of the email.                         | `"Feedback sobre sua candidatura para..."` |
| `body`      | string | The plain text content of the email body.              | `"Agradecemos seu interesse na vaga..."`    |
| `is_new`    | bool   | `True` if the email does not have the processed label. | `True`                                    |

---

## 2. `ExtractedInfo`

Represents the structured data extracted from an email's body by the LLM.

- **Source**: Gemini API call result.
- **Description**: The output of the interpretation step, used to decide whether and how to notify the user. This corresponds to the schema defined in `contracts/gemini-schema.json`.

| Field         | Type   | Description                                                              | Example                   |
|---------------|--------|--------------------------------------------------------------------------|---------------------------|
| `job_related` | bool   | Indicates if the email is related to a job application.                  | `True`                    |
| `empresa`     | string | The name of the company mentioned in the email.                          | `"Acme Corporation"`      |
| `cargo`       | string | The job title mentioned in the email.                                    | `"Software Engineer"`     |
| `resultado`   | enum   | The outcome of the application status. Must be one of `rejeitado`, `avancou`, `indefinido`. | `"rejeitado"` |

---

## 3. `TelegramNotification`

Represents the notification message sent to the user.

- **Source**: Constructed by the bot's notifier module.
- **Description**: The final output of the bot's workflow, sent via the Telegram Bot API.

| Field     | Type   | Description                                         | Example                                           |
|-----------|--------|-----------------------------------------------------|---------------------------------------------------|
| `chat_id` | string | The pre-configured, static ID of the target Telegram chat. | `"123456789"`                                     |
| `text`    | string | The formatted message content.                      | `"❌ Rejeitado — Acme Corporation (Software Engineer)"` |

---

## 4. `ATSConfig`

Represents the configuration for the initial filtering logic.

- **Source**: `config/ats_domains.txt`
- **Description**: A simple list of domains used to perform a "cheap" filter before calling the LLM.

| Field   | Type           | Description                     | Example                          |
|---------|----------------|---------------------------------|----------------------------------|
| `domains` | list[string]   | A list of known ATS domains.    | `["gupy.io", "lever.co", ...]`   |

## State Transitions

The bot is stateless in its own execution environment. State is managed entirely within Gmail.

1.  **Initial State**: Email exists in Gmail without the `jobbot-processado` label.
2.  **Processing**: Bot script runs.
    - Reads email (`is_new: True`).
    - Performs filtering and interpretation.
    - (Optional) Sends Telegram notification.
3.  **Final State**: Bot applies the `jobbot-processado` label to the email via the Gmail API. On the next run, this email is no longer considered new.
