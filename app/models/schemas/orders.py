from app.models.domain.orders import Order
from app.models.schemas.rwschema import RWSchema


class OrderInCreate(RWSchema, Order):
    pass
