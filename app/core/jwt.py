from typing import Dict
from datetime import timedelta

import jwt
from jwt.exceptions import DecodeError, ExpiredSignatureError

from app import settings
from app.models.base import get_utc_now
from app.models.types import PyObjectId
from app.models.schemas.jwt import JWTMeta
from app.models.enums import JWTSubjectEnum


def create_jwt_token(
    *,
    jwt_content: Dict[str, str],
    expires_delta: timedelta,
) -> str:
    to_encode = jwt_content.copy()
    expire = get_utc_now() + expires_delta
    to_encode.update(JWTMeta(exp=expire, subject=JWTSubjectEnum.ACCESS.value).dict())
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm).decode()


def create_access_token_for_user(user_id: PyObjectId) -> str:
    return create_jwt_token(
        jwt_content={"id": str(user_id)},
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
    )


def get_user_id_from_token(token: str) -> str:
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])["id"]
    except DecodeError as decode_error:
        raise ValueError("无法解码该JWT Token") from decode_error
    except ExpiredSignatureError as expired_signature_error:
        raise ValueError("该Token已过期") from expired_signature_error
