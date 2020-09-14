from datetime import datetime, timedelta
from typing import Dict

import jwt

from app import settings
from app.models.schemas.jwt import JWTMeta
from app.models.enums import JWTSubjectEnum


def create_jwt_token(
    *,
    jwt_content: Dict[str, str],
    expires_delta: timedelta,
) -> str:
    to_encode = jwt_content.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update(JWTMeta(exp=expire, subject=JWTSubjectEnum.ACCESS.value).dict())
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm).decode()


def create_access_token_for_user(_id: str) -> str:
    return create_jwt_token(
        jwt_content={"id": _id},
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
    )
