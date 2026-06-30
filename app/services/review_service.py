from fastapi import UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional

from app.config import settings
from app.services.review_logic import get_code_review_from_ollama, split_review_sections


class CodeReview(BaseModel):
    code_smells: Optional[str] = ""
    security_risks: Optional[str] = ""
    performance_concerns: Optional[str] = ""
    readability_architecture: Optional[str] = ""


class ReviewService:
    async def upload_patch(
        self,
        file: Optional[UploadFile] = File(None),
        patch_text: Optional[str] = Form(None),
    ) -> JSONResponse:
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

        if not patch_text or not patch_text.strip():
            raise HTTPException(
                status_code=400,
                detail="Patch content cannot be empty.",
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

        return JSONResponse(status_code=200, content=review_sections)

    async def upload_patch_json(self, payload: dict) -> JSONResponse:
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

        return JSONResponse(status_code=200, content=review_sections)

    async def health_check(self) -> dict:
        return {"status": "ok"}


review_service = ReviewService()
