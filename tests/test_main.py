import io

import pytest
from fastapi.testclient import TestClient
from fastapi import HTTPException

import main

client = TestClient(main.app)

class DummyResponse:
    def __init__(self, status_code=200, json_data=None, text=""):
        self.status_code = status_code
        self._json = json_data or {}
        self.text = text

    def json(self):
        return self._json


def test_split_review_sections_parses_headings():
    review_text = (
        "Code smells:\n"
        "- unused import\n"
        "Security risks:\n"
        "- hardcoded secret\n"
        "Performance concerns:\n"
        "- repeated query\n"
        "Readability & architecture:\n"
        "- unclear naming\n"
    )

    sections = main._split_review_sections(review_text)

    assert sections["code_smells"] == "- unused import"
    assert sections["security_risks"] == "- hardcoded secret"
    assert sections["performance_concerns"] == "- repeated query"
    assert sections["readability_architecture"] == "- unclear naming"


def test_get_code_review_from_ollama_returns_sections(monkeypatch):
    response_text = (
        "Code smells:\n"
        "- duplicate logic\n"
        "Security risks:\n"
        "- injection risk\n"
        "Performance concerns:\n"
        "- heavy loop\n"
        "Readability & architecture:\n"
        "- poor structure\n"
    )

    def fake_post(url, json):
        assert url.endswith("/api/generate")
        assert "Patch:" in json["prompt"]
        return DummyResponse(200, {"response": response_text}, response_text)

    monkeypatch.setattr(main.requests, "post", fake_post)

    sections = main.get_code_review_from_ollama("dummy patch")

    assert sections["code_smells"] == "- duplicate logic"
    assert sections["security_risks"] == "- injection risk"
    assert sections["performance_concerns"] == "- heavy loop"
    assert sections["readability_architecture"] == "- poor structure"


def test_get_code_review_from_ollama_raises_http_exception_on_bad_status(monkeypatch):
    def fake_post(url, json):
        return DummyResponse(500, {"response": ""}, "Internal server error")

    monkeypatch.setattr(main.requests, "post", fake_post)

    with pytest.raises(HTTPException) as exc_info:
        main.get_code_review_from_ollama("dummy patch")

    assert exc_info.value.status_code == 502
    assert "Ollama API error" in exc_info.value.detail


def test_upload_patch_file_success(monkeypatch):
    response_text = (
        "Code smells:\n"
        "- file test\n"
        "Security risks:\n"
        "- none\n"
        "Performance concerns:\n"
        "- none\n"
        "Readability & architecture:\n"
        "- good\n"
    )

    def fake_post(url, json):
        return DummyResponse(200, {"response": response_text}, response_text)

    monkeypatch.setattr(main.requests, "post", fake_post)

    upload_file = ("patch.diff", b"diff --git a/foo b/foo\n")
    response = client.post("/patch/upload", files={"file": upload_file})

    assert response.status_code == 200
    result = response.json()
    assert result["code_smells"] == "- file test"
    assert result["readability_architecture"] == "- good"


def test_upload_patch_form_success(monkeypatch):
    response_text = (
        "Code smells:\n"
        "- patch text\n"
        "Security risks:\n"
        "- none\n"
        "Performance concerns:\n"
        "- none\n"
        "Readability & architecture:\n"
        "- solid\n"
    )

    def fake_post(url, json):
        return DummyResponse(200, {"response": response_text}, response_text)

    monkeypatch.setattr(main.requests, "post", fake_post)

    response = client.post("/patch/upload", data={"patch_text": "diff text"})

    assert response.status_code == 200
    assert response.json()["code_smells"] == "- patch text"


def test_upload_patch_json_success(monkeypatch):
    response_text = (
        "Code smells:\n"
        "- json body\n"
        "Security risks:\n"
        "- none\n"
        "Performance concerns:\n"
        "- none\n"
        "Readability & architecture:\n"
        "- clean\n"
    )

    def fake_post(url, json):
        return DummyResponse(200, {"response": response_text}, response_text)

    monkeypatch.setattr(main.requests, "post", fake_post)

    response = client.post("/patch/upload/json", json={"patch_text": "diff text"})

    assert response.status_code == 200
    assert response.json()["readability_architecture"] == "- clean"


def test_upload_patch_validation_errors():
    response = client.post("/patch/upload", data={})
    assert response.status_code == 400
    assert "Provide either a file upload or patch_text" in response.text

    response = client.post("/patch/upload", data={"patch_text": "   "})
    assert response.status_code == 400
    assert "Patch content cannot be empty" in response.text

    response = client.post("/patch/upload/json", json={"patch_text": ""})
    assert response.status_code == 400
    assert "JSON body must include a non-empty patch_text string" in response.text

    response = client.post("/patch/upload/json", json={"patch_text": None})
    assert response.status_code == 400
    assert "JSON body must include a non-empty patch_text string" in response.text


def test_upload_patch_file_invalid_utf8(monkeypatch):
    def fake_post(url, json):
        return DummyResponse(200, {"response": ""}, "")

    monkeypatch.setattr(main.requests, "post", fake_post)

    upload_file = ("patch.diff", b"\x80\x80\x80")
    response = client.post("/patch/upload", files={"file": upload_file})

    assert response.status_code == 400
    assert "Uploaded file must be UTF-8 encoded text" in response.text


def test_get_code_review_from_ollama_fallback_to_text(monkeypatch):
    raw_text = (
        "Code smells:\n"
        "- fallback logic\n"
        "Security risks:\n"
        "- none\n"
        "Performance concerns:\n"
        "- none\n"
        "Readability & architecture:\n"
        "- fallback parse\n"
    )

    def fake_post(url, json):
        return DummyResponse(200, {"response": ""}, raw_text)

    monkeypatch.setattr(main.requests, "post", fake_post)

    sections = main.get_code_review_from_ollama("dummy patch")
    assert sections["code_smells"] == "- fallback logic"
    assert sections["readability_architecture"] == "- fallback parse"


def test_get_code_review_from_ollama_network_error(monkeypatch):
    def fake_post(url, json):
        raise RuntimeError("connection failed")

    monkeypatch.setattr(main.requests, "post", fake_post)

    with pytest.raises(HTTPException) as exc_info:
        main.get_code_review_from_ollama("dummy patch")

    assert exc_info.value.status_code == 502
    assert "Failed to contact Ollama" in exc_info.value.detail


def test_upload_patch_raises_generic_error(monkeypatch):
    def fake_raise(patch_text):
        raise ValueError("unexpected")

    monkeypatch.setattr(main, "get_code_review_from_ollama", fake_raise)
    response = client.post("/patch/upload", data={"patch_text": "diff text"})

    assert response.status_code == 502
    assert "Error generating code review" in response.text


def test_upload_patch_json_raises_generic_error(monkeypatch):
    def fake_raise(patch_text):
        raise ValueError("unexpected")

    monkeypatch.setattr(main, "get_code_review_from_ollama", fake_raise)
    response = client.post("/patch/upload/json", json={"patch_text": "diff text"})

    assert response.status_code == 502
    assert "Error generating code review" in response.text


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
