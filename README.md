# AI Field Diagnostic

A small FastAPI-based diagnostic workflow that validates equipment issues, gathers local RAG context, and orchestrates a multi-agent diagnostic process.

## Local setup

1. Create a virtual environment and install dependencies:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\python -m pip install -r requirements.txt
   ```

2. Copy the example environment file and set local values:

   ```powershell
   Copy-Item .env.example .env
   ```

3. Populate secrets locally without committing them. Keep `.env` ignored by Git.

## Required environment variables

The app reads the following values at runtime:

- `OPENAI_KEY`: API key for the OpenAI-compatible model client.
- `DIAGNOSTIC_API_KEY`: API key required for `POST /diagnose`.
- `DIAGNOSTIC_TIMEOUT_SECONDS`: optional override for provider timeout.
- `DIAGNOSTIC_RATE_LIMIT_WINDOW_SECONDS`: request window for API throttling.
- `DIAGNOSTIC_RATE_LIMIT_MAX_REQUESTS`: max requests allowed in the window.
- `RAG_DATA_DIR`: approved root for local RAG ingestion.

See [.env.example](.env.example) for placeholder values.

## Run locally

```powershell
.\.venv\Scripts\python run.py
```

Then open the app at `http://localhost:8000`.

## Test suite

```powershell
.\.venv\Scripts\python -m pytest -q
```

The suite is designed to run without a live OpenAI API key. Tests mock external dependencies and exercise degraded RAG and dependency failure handling locally.

## API authentication and rate limiting

- `POST /diagnose` requires the `X-API-Key` header.
- Invalid or missing keys return `401`.
- Excessive requests return `429` with a `Retry-After` header.

## RAG ingestion

- Local ingestion is restricted to an approved root directory.
- Symlinks and files outside the configured root are rejected.
- This prevents path traversal and unsafe document ingestion.

## Failure handling

The workflow preserves the current production-safe behavior:

- provider timeout failures are classified to predictable user-facing responses
- unsupported or malformed agent output is rejected without being silently accepted
- RAG failures degrade gracefully and annotate the final result
- raw secrets, prompts, and provider internals are not exposed to API clients

## Production note

This project is not meant to ship with a real API key stored in the repository. Keep credentials in the local environment and rotate any previously exposed tokens before production use.
