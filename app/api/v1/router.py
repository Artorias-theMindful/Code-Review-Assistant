from fastapi import APIRouter

from app.services.review_service import review_service

router = APIRouter()

router.post("/patch/upload")(review_service.upload_patch)
router.post("/patch/upload/json")(review_service.upload_patch_json)
router.get("/health")(review_service.health_check)
