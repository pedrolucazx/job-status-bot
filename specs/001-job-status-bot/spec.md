# Feature Specification: Job Status Bot

**Feature Branch**: `001-job-status-bot`

**Created**: 2026-07-17

**Status**: Draft

**Input**: User description: "Bot que lê a caixa do Gmail (`pedrolucazxmesquita@gmail.com`), identifica emails de processos seletivos (rejeição / avanço de etapa) e notifica o candidato via Telegram."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Receive Rejection Notification (Priority: P1)

As a job applicant, I want to be automatically notified via Telegram when a company rejects my application, so I can keep my application records updated without manually checking my email for status changes.

**Why this priority**: This is a core function of the bot, providing immediate value by filtering email noise and delivering a clear, actionable outcome.

**Independent Test**: Can be fully tested by sending a mock rejection email (e.g., from `mail.gupy.io`) to the target Gmail account and verifying that a correctly formatted "❌ Rejeitado" message is received in the specified Telegram chat.

**Acceptance Scenarios**:

1. **Given** a new email from a known ATS domain contains keywords indicating rejection, **When** the bot runs, **Then** it sends a Telegram message formatted as `❌ Rejeitado — <Empresa> (<Cargo>)`.
2. **Given** a new email is processed as a rejection, **When** the bot runs again, **Then** the same email is not processed a second time.

---

### User Story 2 - Receive Advancement Notification (Priority: P1)

As a job applicant, I want to be automatically notified via Telegram when a company advances my application to the next stage, so I am aware of the positive progress and can anticipate further communication.

**Why this priority**: This is the other core function of the bot, providing timely and positive feedback that is crucial for the user's job search process.

**Independent Test**: Can be fully tested by sending a mock "next steps" email to the target Gmail account and verifying that a correctly formatted "✅ Avançou de etapa" message is received in the specified Telegram chat.

**Acceptance Scenarios**:

1. **Given** a new email from any source contains keywords indicating advancement in a hiring process, **When** the bot runs, **Then** it sends a Telegram message formatted as `✅ Avançou de etapa — <Empresa> (<Cargo>)`.
2. **Given** a new email is processed as an advancement, **When** the bot adds the `jobbot-processado` label, **Then** the bot does not process the email again.

---

### User Story 3 - Ignore Irrelevant Emails (Priority: P2)

As a bot user, I want the system to intelligently ignore emails that are not related to job application statuses (e.g., newsletters, spam, application confirmations without a verdict), so my Telegram notifications are not cluttered with irrelevant information.

**Why this priority**: This ensures the bot provides a high-quality, low-noise signal, which is critical for user retention and trust.

**Independent Test**: Can be tested by sending various non-status emails (e.g., a marketing newsletter, a simple application confirmation email) and verifying that no notification is sent to Telegram, but the emails are still labeled as processed.

**Acceptance Scenarios**:

1. **Given** a new email is a newsletter, **When** the bot runs, **Then** no Telegram message is sent, and the email is labeled `jobbot-processado`.
2. **Given** a new email only confirms receipt of an application ("Obrigado por se candidatar"), **When** the bot runs, **Then** the Gemini API returns `resultado: "indefinido"` and no Telegram message is sent.

### Edge Cases

- What happens when an email contains both advancement and rejection keywords? (The LLM's judgment will be the deciding factor).
- How does the system handle rate limits from Gmail, Gemini, or Telegram APIs? (The cron schedule is the primary mitigation; more robust error handling could be a V2 feature).
- What happens if the email body is malformed, encrypted, or empty? (The LLM should return `job_related: false` or `resultado: "indefinido"`).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST run on a recurring schedule using GitHub Actions (`schedule: cron`).
- **FR-002**: System MUST authenticate with the Google API using provided OAuth credentials to access a specific Gmail account.
- **FR-003**: System MUST search for emails that do not have the `jobbot-processado` label.
- **FR-004**: System MUST perform an initial, non-AI filter to identify potentially relevant emails based on sender domain (from a configurable list of ATS providers) or subject line keywords.
- **FR-005**: System MUST use the Gemini API to perform structured data extraction on the body of filtered emails, identifying at least: `job_related`, `empresa`, `cargo`, and `resultado`.
- **FR-006**: System MUST send a notification to a pre-configured Telegram `CHAT_ID` if the extracted `resultado` is `rejeitado` or `avancou`.
- **FR-007**: System MUST NOT send a Telegram notification if the extracted `resultado` is `indefinido` or `job_related` is `false`.
- **FR-008**: System MUST apply the `jobbot-processado` label to every email it inspects to prevent reprocessing, regardless of the outcome.
- **FR-009**: System MUST NOT write, delete, or modify any email content beyond applying the label.

### Key Entities

- **Email**: The input data object, containing a sender, subject, and body. It is the source of state.
- **ATS Domain List**: A configurable list of domains used for the initial "cheap filter".
- **Notification**: The output data object sent to Telegram, containing a clear result (`❌` or `✅`), company name, and role.
- **API Credentials**: A set of secrets (`GMAIL_CLIENT_ID`, `GEMINI_API_KEY`, etc.) required for authenticating with external services.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 95% of job application rejection emails from the top 5 listed ATS domains are correctly identified and trigger a Telegram notification within one processing cycle.
- **SC-002**: 95% of job application advancement emails containing common keywords ("next steps", "próxima etapa", "entrevista") are correctly identified and trigger a Telegram notification.
- **SC-003**: Fewer than 5% of processed emails that are not related to job application status changes result in a false-positive notification.
- **SC-004**: 100% of processed emails are successfully labeled `jobbot-processado` and are not processed in subsequent runs of the bot.
- **SC-005**: The bot successfully runs to completion via GitHub Actions cron job without runtime errors for at least 24 hours.

## Assumptions

- All necessary credentials (`GMAIL_CLIENT_ID`, `GMAIL_CLIENT_SECRET`, `GMAIL_REFRESH_TOKEN`, `GEMINI_API_KEY`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`) are correctly configured as secrets in the GitHub repository.
- The target Gmail account has a `jobbot-processado` label already created.
- The cron schedule (`*/10 * * * *` or similar) is infrequent enough to stay within the free tier limits of the Gmail and Gemini APIs.
- The "job-search" repo workflow, where the user manually inputs application data into Notion, exists and works as described, but this bot has no direct interaction with it.
