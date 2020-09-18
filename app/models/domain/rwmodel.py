import datetime

from bson import ObjectId, Decimal128
from pydantic import BaseModel, BaseConfig


def convert_datetime_to_str(dt: datetime.datetime) -> str:
    return dt.replace(tzinfo=datetime.timezone.utc).isoformat().replace("+00:00", "Z")


class RWModel(BaseModel):
    """模型基类."""
    class Config(BaseConfig):
        allow_population_by_field_name = True
        json_encoders = {
            datetime.datetime: convert_datetime_to_str,
            ObjectId: lambda x: x.__str__(),
            Decimal128: lambda x: float(x.__str__()),
        }
