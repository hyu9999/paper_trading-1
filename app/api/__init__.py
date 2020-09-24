from fastapi import APIRouter

from app.api.routes import authentication, users, orders, position


router = APIRouter()
router.include_router(authentication.router, tags=["authentication"], prefix="/auth")
router.include_router(users.router, tags=["user"], prefix="/users")
router.include_router(orders.router, tags=["order"], prefix="/orders")
router.include_router(position.router, tags=["position"], prefix="/position")
