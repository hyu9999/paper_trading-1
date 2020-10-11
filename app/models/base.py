from datetime import datetime, timezone, timedelta

from bson import ObjectId
from pydantic import BaseModel, Field

from app.models.types import PyObjectId


def get_utc_now():
    return datetime.now(timezone(timedelta(hours=8)))


class DateTimeModelMixin(BaseModel):
    created_at: datetime = Field(default_factory=get_utc_now)
    updated_at: datetime = Field(default_factory=get_utc_now)


class DBModelMixin(DateTimeModelMixin):
    id: PyObjectId = Field(default_factory=ObjectId, alias="_id")
