from fastapi import APIRouter


router = APIRouter()


@router.get("", response_model=None, name="users:")
async def foo():
    pass
