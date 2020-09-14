from fastapi import APIRouter

from app.api.routes import authentication


router = APIRouter()
router.include_router(authentication.router, tags=["authentication"], prefix="/users")

