from app.models.schemas.rwschema import RWSchema


class Log(RWSchema):
    msg: str
    level: int
