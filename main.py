from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import os
from dotenv import load_dotenv
import requests

load_dotenv()

app = FastAPI(
    title="Code Review Assistant Patch Upload API",
    description="Upload git diffs or PR patch files and get parsed metadata back.",
    version="1.0.0",
)


class CodeReview(BaseModel):
    code_smells: Optional[str] = ""
    security_risks: Optional[str] = ""
    performance_concerns: Optional[str] = ""
    readability_architecture: Optional[str] = ""


def _split_review_sections(text: str) -> dict:
    sections = {
        "code_smells": "",
        "security_risks": "",
        "performance_concerns": "",
        "readability_architecture": "",
    }

    # naive split by headings
    lowers = text.replace('\r', '').split('\n')
    current = None
    mapping = {
        "code smells": "code_smells",
        "security risks": "security_risks",
        "performance concerns": "performance_concerns",
        "readability": "readability_architecture",
        "readability & architecture": "readability_architecture",
        "readability and architecture": "readability_architecture",
    }
    for line in lowers:
        key = line.strip().lower()
        if any(k in key for k in mapping.keys()):
            # find matching mapping key
            for k, v in mapping.items():
                if k in key:
                    current = v
                    break
            continue
        if current:
            sections[current] += (line + "\n")
    # strip
    for k in sections:
        sections[k] = sections[k].strip()

    return sections


def get_code_review_from_ollama(patch_text: str) -> dict:

    ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
    model = os.getenv("OLLAMA_MODEL", "gemma4")
    prompt = (
        "You are an expert code reviewer. Given the following git patch, produce "
        "concise sections:\n"
        "1) Code smells\n"
        "2) Security risks\n"
        "3) Performance concerns\n"
        "4) Readability & architecture\n\n"
        "Patch:\n"
        + patch_text
    )

    try:
        endpoint = ollama_url.rstrip("/") + "/api/generate"
        resp = requests.post(
            endpoint,
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {"num_predict": 1024},
            },
        )
        print(resp.json())
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to contact Ollama: {e}")

    if resp.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail=f"Ollama API error: {resp.status_code} {resp.text}",
        )

    # try to extract text from JSON response, fallback to raw text
    review_text = resp.json()["response"]

    if not review_text:
        review_text = resp.text or ""

    sections = _split_review_sections(review_text)
    return sections


@app.post("/patch/upload", response_model=CodeReview)
async def upload_patch(
    file: Optional[UploadFile] = File(None),
    patch_text: Optional[str] = Form(None),
):
    """Upload a git diff or PR patch as a file or raw text."""
    if file is None and patch_text is None:
        raise HTTPException(
            status_code=400,
            detail="Provide either a file upload or patch_text form field.",
        )

    if file is not None:
        payload = await file.read()
        try:
            patch_text = payload.decode("utf-8")
        except UnicodeDecodeError:
            raise HTTPException(
                status_code=400,
                detail="Uploaded file must be UTF-8 encoded text.",
            )

    # generate code review via Ollama
    try:
        review_sections = get_code_review_from_ollama(patch_text)
    except HTTPException:
        # bubble up Ollama-related HTTPException
        raise
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Error generating code review: {e}",
        )

    review = review_sections
    return JSONResponse(status_code=200, content=review)


@app.post("/patch/upload/json", response_model=CodeReview)
async def upload_patch_json(payload: dict):
    """Upload a git diff or PR patch as JSON with a `patch_text` key."""
    patch_text = payload.get("patch_text")
    if not isinstance(patch_text, str) or not patch_text.strip():
        raise HTTPException(
            status_code=400,
            detail="JSON body must include a non-empty patch_text string.",
        )

    try:
        review_sections = get_code_review_from_ollama(patch_text)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Error generating code review: {e}",
        )

    review = review_sections
    return JSONResponse(status_code=200, content=review)


@app.get("/health")
async def health_check():
    return {"status": "ok"}
