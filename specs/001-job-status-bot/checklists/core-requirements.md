# Checklist: Core Requirements Quality

**Purpose**: This checklist validates the quality and completeness of the core requirements for the Job Status Bot, ensuring the specification is clear and robust before implementation begins.
**Created**: 2026-07-17
**Feature**: [Link to spec.md](./spec.md)

## Requirement Completeness

- [ ] CHK001 - Does the spec explicitly state that the "cheap filter" keywords for email subjects are configurable, similar to the ATS domains? [Gap]
- [ ] CHK002 - Are there requirements defining the bot's behavior if the `jobbot-processado` label does not exist in the user's Gmail account? [Completeness, Gap]
- [ ] CHK003 - Are the requirements for handling Gmail API authentication failures (e.g., expired/revoked refresh token) specified? [Coverage, Gap]
- [ ] CHK004 - Does the spec define the format and inclusion criteria for the optional "link to original email" in the Telegram notification? [Clarity, Spec §5]
- [ ] CHK005 - Are there requirements for logging the bot's actions, such as emails processed, results from the LLM, and notifications sent? [Gap]

## Requirement Clarity

- [ ] CHK006 - Is the definition of an `indefinido` result from the LLM clear enough to ensure that emails confirming application receipt *without* a verdict are consistently ignored? [Clarity, Spec §4, §5]
- [ ] CHK007 - Is the list of subject-line keywords for the initial "cheap filter" explicitly defined or marked as a required configuration item? [Clarity, Spec §3]
- [ ] CHK008 - Does the `95%` success criterion for email identification have a clearly defined measurement methodology? (e.g., tested against a golden set of 100 sample emails) [Measurability, Spec §SC-001]

## Scenario & Edge Case Coverage

- [ ] CHK009 - Does the spec define the required behavior if a Gemini API call fails, times out, or returns a malformed response? [Coverage, Exception Flow]
- [ ] CHK010 - Does the spec require a specific behavior if sending the notification to Telegram fails (e.g., should the bot retry, or simply log the error and move on)? [Coverage, Exception Flow]
- [ ] CHK011 - Are there requirements for handling emails with bodies that are empty, encrypted, or too large for the Gemini API's context window? [Coverage, Edge Case, Spec §Edge Cases]
- [ ] CHK012 - Is the behavior defined for when an email matches the "cheap filter" but the LLM determines it is not job-related (`job_related: false`)? (The spec implies it's just labeled and ignored, but this should be explicit). [Clarity, Spec §3, §5]
- [ ] CHK013 - Does the spec clarify the expected outcome if the same email is received multiple times (e.g., as part of a forwarded chain)? [Coverage, Edge Case]

## Dependencies & Assumptions

- [ ] CHK014 - Does the spec require validation that all necessary secrets and environment variables are present at startup? [Assumption, Gap]
- [ ] CHK015 - Is the assumption that the cron schedule is sufficient to avoid rate limits validated, or are there requirements for the bot to handle 429 (Too Many Requests) errors gracefully? [Assumption, Spec §Edge Cases]
