# Code Review Assistant

A lightweight FastAPI service for uploading git patch files or raw patch text and generating a structured code review summary.

## Project Structure

```text
code-review-assistant/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── dependencies.py
│   ├── exceptions.py
│   ├── middleware.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── router.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── router.py
│   │   └── v2/
│   │       └── __init__.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── review_service.py
│   │   ├── review_logic.py
│   └── core/
│       ├── __init__.py
│       └── logging.py
├── tests/
│   ├── test_app.py
├── pyproject.toml
└── .env.example
```

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
- `fastapi`
- `requests`
- `python-dotenv`
- `uvicorn`

## Setup

1. Create and activate a virtual environment:

```bash
cd /Users/arttemlunev/Documents/Code-Review-Assistant
python -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:

```bash
python -m pip install -r requirements.txt
```

3. Install development dependencies:

```bash
python -m pip install -r requirements-dev.txt
```

4. Copy the example environment file:

```bash
cp .env.example .env
```

## Configuration

The service reads these environment variables from `.env`:

- `OLLAMA_URL` - Ollama server endpoint
- `OLLAMA_MODEL` - Ollama model name

## Running the app

Start the FastAPI application:

```bash
uvicorn app.main:app --reload
```

The service will be available at `http://127.0.0.1:8000`.

## API Endpoints

### POST /api/v1/patch/upload

Accepts either a multipart file upload or a form field named `patch_text`.

- `file` - patch file as multipart upload
- `patch_text` - raw patch text as form input

### POST /api/v1/patch/upload/json

Accepts JSON payload with a `patch_text` string.

Example:

```json
{
  "patch_text": "diff --git a/foo b/foo..."
}
```

### GET /api/v1/health

Returns:

```json
{ "status": "ok" }
```

## Tests

Run the full test suite with coverage:

```bash
python -m pytest --cov=app --cov-report=term-missing
```

## Linting

Run Flake8 across the project:

```bash
flake8 .
```

## Notes

- `.env` is used for local configuration and should not be committed.
