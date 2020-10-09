from decimal import Decimal
from typing import Any, Dict, Union

from bson import ObjectId, Decimal128

from app.models.typing import CallableGenerator


class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls) -> 'CallableGenerator':
        yield cls.validate

    @classmethod
    def __modify_schema__(cls, field_schema: Dict[str, Any]) -> None:
        field_schema.update(pattern="^[0-9a-fA-F]{24}$", examples=["5f365bedcf31136279a97d19",
                                                                   "5d883e0bedcac5082ecf3afa"])

    @classmethod
    def validate(cls, v: Any) -> Any:
        if not isinstance(v, cls):
            if not cls.is_valid(v):
                raise TypeError(f"Not a valid ObjectId: {v}")
            return cls(v)
        return cls(v)


class PyDecimal(Decimal128):
    @classmethod
    def __get_validators__(cls) -> 'CallableGenerator':
        yield cls.validate

    @classmethod
    def __modify_schema__(cls, field_schema: Dict[str, Any]) -> None:
        field_schema.update(type='number', format='json-number')

    @classmethod
    def validate(cls, v: Union[float, int, Decimal]) -> Any:
        """转化float为Decimal128.

        先将python的二进制浮点数用str方法显式的转化为10进制浮点数，再把10进制浮点数字符串转化为Decimal128.
        """
        return cls(str(v))
