# Research: Job Status Bot

**Date**: 2026-07-17

**Prerequisite**: [plan.md](./plan.md)

## Objective

This document outlines the decisions made regarding the primary dependencies for the Job Status Bot, confirming they align with the project's principles of simplicity and standard tooling. The initial `SPEC.md` was clear, so no major unknowns required deep research.

---

## 1. Gmail API Integration

- **Technology**: `google-api-python-client` and `google-auth`
- **Decision**: Proceed with the official Google Python client libraries.
- **Rationale**: These are the standard, well-documented, and officially supported libraries for interacting with Google services, including Gmail. They handle the complexities of OAuth 2.0 and provide a stable interface for searching messages and modifying labels. Using the official library is the simplest and most robust approach.
- **Alternatives considered**:
    - **Raw `requests` calls**: This would require manually handling the entire OAuth 2.0 flow (token refreshing, etc.) and constructing API requests. It adds unnecessary complexity and maintenance overhead, violating the simplicity principle.

---

## 2. LLM for Email Interpretation

- **Technology**: `google-generativeai` (Gemini API)
- **Decision**: Use the Gemini API via the official Python SDK for structured data extraction.
- **Rationale**: The `SPEC.md` requires structured JSON output (`{ "job_related": ..., "resultado": ... }`), and modern LLMs like Gemini are well-suited for this "function calling" or structured extraction task. The free tier is sufficient for the MVP's scale. The `google-generativeai` library is the simplest way to interact with the API.
- **Alternatives considered**:
    - **Regex/Keyword-based parsing**: This approach is brittle and cannot reliably handle the wide variety of phrasing in emails from different companies. It would lead to poor accuracy and a frustrating user experience. An LLM is necessary for the required level of understanding.

---

## 3. Telegram Notifications

- **Technology**: `requests` library
- **Decision**: Use the `requests` library to make a direct POST request to the Telegram Bot API's `sendMessage` endpoint.
- **Rationale**: The `sendMessage` endpoint is a simple, stateless HTTP request. A dedicated Telegram library would be an unnecessary dependency for this single use case, violating the Ponytail principle. A direct `requests` call is minimal, clear, and sufficient.
- **Alternatives considered**:
    - **`python-telegram-bot`**: A powerful library, but it's designed for building complex, interactive bots with long-polling or webhooks. It is overkill for sending a single, one-way notification.

---

## Conclusion

All technology choices from the initial `SPEC.md` are validated. They represent the simplest, most direct, and most maintainable path for the MVP, fully aligning with the project's constitution. No NEEDS CLARIFICATION markers were present in the plan, so design can proceed directly.
