import time
from datetime import timedelta
from typing import Optional

import jwt
import pytest
from dynaconf import Dynaconf

from app.core.jwt import create_jwt_token, get_user_id_from_token

jwt_content = {"id": "test_id"}


@pytest.fixture
def token():
    token = create_jwt_token(
        jwt_content=jwt_content, expires_delta=timedelta(seconds=2)
    )
    return token


@pytest.fixture
def invalid_token(token: str):
    return token[::-1]


def test_create_jwt_token(settings: Dynaconf):
    token = create_jwt_token(
        jwt_content=jwt_content, expires_delta=timedelta(minutes=1)
    )
    content = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    assert content["id"] == jwt_content["id"]


@pytest.mark.parametrize(
    "expect_exception_message, time_sleep, jwt_token",
    [
        ("", 0, pytest.lazy_fixture("token")),
        ("无法解码该JWT Token.", 0, pytest.lazy_fixture("invalid_token")),
        ("该Token已过期.", 3, pytest.lazy_fixture("token")),
    ],
)
def test_decode_jwt_token(
    expect_exception_message: Optional[Exception], time_sleep: int, jwt_token: str
):
    time.sleep(time_sleep)
    exp = ""
    try:
        id_ = get_user_id_from_token(jwt_token)
    except Exception as e:
        exp = e
    else:
        assert id_ == jwt_content["id"]
    assert str(exp) == expect_exception_message
