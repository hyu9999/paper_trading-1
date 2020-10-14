from app.models.base import get_utc_now

position_in_create_json = {
    "symbol": "601816",
    "exchange": "SH",
    "volume": 100,
    "available_volume": 0,
    "cost": "10",
    "current_price": "10",
    "profit": "0",
    "first_buy_date": get_utc_now()
}
