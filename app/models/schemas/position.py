from app.models.schemas.rwschema import RWSchema
from app.models.domain.position import PositionInDB, Position


class PositionInCreate(RWSchema, PositionInDB):
    pass


class PositionInResponse(RWSchema, Position):
    pass
