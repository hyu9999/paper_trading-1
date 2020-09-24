from app.models.schemas.rwschema import RWSchema


class Log(RWSchema):
    content: str
    level: str
