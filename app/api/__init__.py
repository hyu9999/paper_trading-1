from fastapi import APIRouter

from app.api.routes import authentication, users


router = APIRouter()
router.include_router(authentication.router, tags=["authentication"], prefix="/auth")
router.include_router(users.router, tags=["user"], prefix="/users")
