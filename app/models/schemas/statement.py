from app.models.types import Decimal128
from app.models.domain.statement import Costs
from app.models.domain.orders import OrderInDB
from app.models.schemas.rwschema import RWSchema


class StatementInCreateEvent(RWSchema):
    costs: Costs
    order: OrderInDB
    securities_diff: Decimal128
