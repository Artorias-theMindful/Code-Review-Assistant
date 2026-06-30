# Code Review Assistant

A lightweight FastAPI service for uploading git patch files or raw patch text and generating a structured code review summary.

## Features

- Accepts patch uploads via multipart file upload
- Accepts patch text via form field or JSON payload
- Calls an Ollama model to generate review sections
- Returns structured review output for:
  - Code smells
  - Security risks
  - Performance concerns
  - Readability & architecture
- Includes a health check endpoint

## Requirements

- Python 3.14
- `requests`
- `fastapi`
- `uvicorn`
- `python-dotenv`

## Setup

1. Create and activate a virtual environment:

```bash
cd /Users/artemlunev/Documents/Code-Review-Assistant
python -m venv .venv
source .venv/bin/activate
```

2. Install the application dependencies:

```bash
python -m pip install -r requirements.txt
```

3. Install development dependencies for tests and linting:

```bash
python -m pip install -r requirements-dev.txt
```

4. Copy the environment example to `.env` if needed:

```bash
cp .env.example .env
```

## Configuration

The service reads these environment variables from `.env`:

- `OLLAMA_URL` - Ollama server endpoint (default: `http://localhost:11434`)
- `OLLAMA_MODEL` - Ollama model name to use (default: `gemma4`)

## Running the app

Start the FastAPI application with Uvicorn:

```bash
uvicorn main:app --reload
```

The service will be available at `http://127.0.0.1:8000`.

## API Endpoints

### POST /patch/upload

Accepts either a multipart file upload or a form field named `patch_text`.

- `file` - patch file as multipart upload
- `patch_text` - raw patch text as form input

### POST /patch/upload/json

Accepts JSON payload with a `patch_text` string.

Example:

```json
{
  "patch_text": "diff --git a/foo b/foo..."
}
```

### GET /health

Returns:

```json
{ "status": "ok" }
```

## Tests

Run the full test suite with coverage:

```bash
python -m pytest --cov=main --cov-report=term-missing
```

## Linting

Run Flake8 across the project:

```bash
flake8 .
```

## Notes

- `.env` is used for local configuration and should not be committed.
- The project includes `tests/conftest.py` to ensure the project root is available during pytest collection.
