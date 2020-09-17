from datetime import datetime

from bson import ObjectId
from pydantic import BaseModel, Field

from app.models.types import PyObjectId


class DateTimeModelMixin(BaseModel):
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class DBModelMixin(DateTimeModelMixin):
    id: PyObjectId = Field(default_factory=ObjectId, alias="_id")
