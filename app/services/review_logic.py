import os
import requests

from app.config import settings


def split_review_sections(text: str) -> dict:
    sections = {
        "code_smells": "",
        "security_risks": "",
        "performance_concerns": "",
        "readability_architecture": "",
    }

    lowers = text.replace("\r", "").split("\n")
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
            for k, v in mapping.items():
                if k in key:
                    current = v
                    break
            continue
        if current:
            sections[current] += line + "\n"

    for k in sections:
        sections[k] = sections[k].strip()

    return sections


def get_code_review_from_ollama(patch_text: str) -> dict:
    ollama_url = settings.ollama_url
    model = settings.ollama_model
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
    except Exception as e:
        raise RuntimeError(f"Failed to contact Ollama: {e}")

    if resp.status_code != 200:
        raise RuntimeError(f"Ollama API error: {resp.status_code} {resp.text}")

    review_text = resp.json().get("response", "")
    if not review_text:
        review_text = resp.text or ""

    return split_review_sections(review_text)
