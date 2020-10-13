import sys
from typing import Optional

import pytest
from bson import ObjectId
from fastapi import FastAPI, Depends
from httpx import AsyncClient
from dynaconf import Dynaconf

from app.api.dependencies.authentication import get_current_user_authorizer
from app.exceptions.http import AuthHeaderNotFound, _HTTPException, WrongTokenFormat, InvalidAuthTokenPrefix, \
    InvalidAuthToken, InvalidUserID
from app.models.domain.users import UserInDB

pytestmark = pytest.mark.asyncio


random_object_id = ObjectId()


@pytest.mark.skipif(sys.platform == "linux", reason="在test workflow中跳过此测试")
@pytest.mark.parametrize(
    "auth_header, exception",
    [
        ({}, AuthHeaderNotFound),
        ({"Authorization": "WRONG TOKEN FORMAT"}, WrongTokenFormat),
        ({"Authorization": "INVALID TOKEN"}, InvalidAuthTokenPrefix),
        ({"Authorization": "Token TOKEN"}, InvalidAuthToken),
        ({"Authorization": f"Token {random_object_id}"}, InvalidUserID),
        ({}, None)
    ],
)
async def test_get_current_user(
    initialized_app: FastAPI,
    settings: Dynaconf,
    auth_header: dict,
    exception: Optional[_HTTPException],
    test_user: UserInDB,
):
    @initialized_app.get("/test_auth_depend")
    def get_user(_user: UserInDB = Depends(get_current_user_authorizer())):
        return str(_user.id)

    headers = {"Content-Type": "application/json"}
    if not exception:
        auth_header = {"Authorization": f"Token {str(test_user.id)}"}
    headers.update(auth_header)
    async with AsyncClient(
        app=initialized_app,
        base_url=settings.base_url,
        headers=headers,
    ) as client:
        response = await client.get("/test_auth_depend")
        if exception:
            assert response.json()["code"] == exception.code
        else:
            assert response.json() == str(test_user.id)
