import time
from typing import Optional
from datetime import timedelta

import jwt
import pytest
from dynaconf import Dynaconf
from jwt.exceptions import DecodeError, ExpiredSignatureError

from app.core.jwt import create_jwt_token, get_user_id_from_token

jwt_content = {"id": "test_id"}


@pytest.fixture
def token():
    token = create_jwt_token(jwt_content=jwt_content, expires_delta=timedelta(seconds=3))
    return token


def test_create_jwt_token(settings: Dynaconf):
    token = create_jwt_token(jwt_content=jwt_content, expires_delta=timedelta(minutes=1))
    content = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    assert content["id"] == jwt_content["id"]


@pytest.mark.parametrize(
    "expect_exception",
    [None, DecodeError, ExpiredSignatureError]
)
def test_decode_jwt_token(token: str, expect_exception: Optional[Exception]):
    if expect_exception == ExpiredSignatureError:
        time.sleep(3)
    try:
        id_ = get_user_id_from_token(token)
    except Exception as e:
        assert e == expect_exception
    else:
        assert id_ == jwt_content["id"]
