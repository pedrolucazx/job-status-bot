# Tasks: Job Status Bot

**Input**: Design documents from `/specs/001-job-status-bot/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Test tasks are included as they are referenced in the `plan.md` project structure.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- Paths assume the single project structure defined in `plan.md`.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure.

- [X] T001 [P] Create project directory structure: `src/bot`, `src/config`, `src/utils`, `tests/integration`, `tests/unit`.
- [X] T002 [P] Create `requirements.txt` with primary dependencies: `google-api-python-client`, `google-auth`, `google-generativeai`, `requests`, `python-dotenv`.
- [X] T003 [P] Create configuration file `src/config/ats_domains.txt` with the initial list of ATS domains from `SPEC.md`.
- [X] T004 [P] Create empty `__init__.py` files in `src/`, `src/bot/`, `src/utils/`, `src/config/`, `tests/`, `tests/unit/`, `tests/integration/`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T005 Implement Google authentication helper in `src/utils/auth.py` to handle OAuth2 credential loading from environment variables and refresh tokens.
- [ ] T006 [P] Create placeholder classes and methods for `GmailClient` in `src/bot/gmail_client.py`, `LLMHandler` in `src/bot/llm_handler.py`, and `Notifier` in `src/bot/notifier.py`.
- [ ] T007 Create the main entry point script `src/bot/main.py` with argument parsing for `--local-email` and basic orchestration logic structure.

**Checkpoint**: Foundation ready - user story implementation can now begin.

---

## Phase 3: User Story 1 - Receive Rejection Notification (Priority: P1) 🎯 MVP

**Goal**: Implement the end-to-end flow for identifying, parsing, and sending a notification for a job rejection email.

**Independent Test**: Send a mock rejection email to the system and verify a "❌ Rejeitado" message is received on Telegram.

### Tests for User Story 1

- [ ] T008 [P] [US1] Write a unit test in `tests/unit/test_notifier.py` to mock the `requests.post` call and verify the `Notifier` sends a correctly formatted message.
- [ ] T009 [P] [US1] Write a unit test in `tests/unit/test_llm_handler.py` to check that the handler correctly calls the Gemini client with the right prompt and schema.

### Implementation for User Story 1

- [ ] T010 [P] [US1] Implement the `Notifier.send_message` method in `src/bot/notifier.py` to send a POST request to the Telegram API.
- [ ] T011 [US1] Implement the `LLMHandler.extract_info` method in `src/bot/llm_handler.py` to call the Gemini API with the email body and the JSON schema from `contracts/gemini-schema.json`.
- [ ] T012 [US1] Implement the `GmailClient.get_new_emails` method in `src/bot/gmail_client.py` to search for emails without the `jobbot-processado` label using the Gmail API. (Depends on T005)
- [ ] T013 [US1] Implement the `GmailClient.apply_label` method in `src/bot/gmail_client.py` to add the `jobbot-processado` label to a message by its ID.
- [ ] T014 [US1] Implement the core processing loop in `src/bot/main.py` to orchestrate the flow for a single email: get email -> extract info -> send notification if `resultado == 'rejeitado'` -> apply label.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently using the `quickstart.md` guide.

---

## Phase 4: User Story 2 - Receive Advancement Notification (Priority: P1)

**Goal**: Extend the existing logic to handle "advancement" emails.

**Independent Test**: Send a mock "next steps" email and verify a "✅ Avançou de etapa" message is received on Telegram.

### Implementation for User Story 2

- [ ] T015 [US2] Update the core processing loop in `src/bot/main.py` to handle the `resultado == 'avancou'` case and format the correct `✅ Avançou de etapa...` message.

**Checkpoint**: User Stories 1 and 2 should both work.

---

## Phase 5: User Story 3 - Ignore Irrelevant Emails (Priority: P2)

**Goal**: Refine the logic to explicitly ignore emails that the LLM marks as `indefinido`.

**Independent Test**: Send a mock application confirmation email and verify NO message is sent to Telegram, but the email is still processed.

### Implementation for User Story 3

- [ ] T016 [US3] Update the core processing loop in `src/bot/main.py` to ensure no notification is sent if `job_related` is `false` or `resultado` is `indefinido`.

**Checkpoint**: All user stories should now be independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Finalize the project for deployment and maintenance.

- [ ] T017 [P] Create the GitHub Actions workflow file `.github/workflows/poll.yml` with the `schedule: cron` trigger.
- [ ] T018 [P] Write a `README.md` for the project, including setup instructions from `quickstart.md` and an overview of the architecture.
- [ ] T019 [P] Write a unit test in `tests/unit/test_gmail_client.py` to mock the Gmail API service and verify `get_new_emails` and `apply_label` construct the correct API calls.
- [ ] T020 Run `pip freeze > requirements.txt` to lock final dependencies.
- [ ] T021 Perform a final code cleanup, add comments where necessary, and ensure all local test cases pass.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Can start immediately.
- **Foundational (Phase 2)**: Depends on Setup completion.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion.
- **Polish (Phase 6)**: Depends on all user stories being complete.

### User Story Dependencies

- **User Story 1 (P1)**: Depends on Foundational (Phase 2).
- **User Story 2 (P2)**: Depends on User Story 1 components.
- **User Story 3 (P3)**: Depends on User Story 1 components.

### Implementation Strategy

- **MVP First**: Complete Phases 1, 2, and 3 to deliver the core rejection-notification functionality.
- **Incremental Delivery**: Complete Phase 4 (Advancement) and Phase 5 (Ignoring) in order, as they build upon the MVP.
- **Finalization**: Complete Phase 6 to prepare for deployment.
