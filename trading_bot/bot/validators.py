from enum import Enum
from typing import Optional
from bot.logging_config import logger

class OrderSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"

class OrderType(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP_MARKET = "STOP_MARKET"

def validate_symbol(symbol: str) -> str:
    # Basic validation formatting
    valid_symbol = symbol.strip().upper()
    if not valid_symbol:
        raise ValueError("Symbol cannot be empty.")
    if len(valid_symbol) < 3:
        raise ValueError(f"Invalid symbol '{valid_symbol}'. Must be at least 3 characters.")
    return valid_symbol

def validate_quantity(quantity: float) -> float:
    if quantity <= 0:
        raise ValueError("Quantity must be greater than zero.")
    return quantity

def validate_price(order_type: OrderType, price: Optional[float] = None) -> Optional[float]:
    if order_type == OrderType.LIMIT:
        if price is None or price <= 0:
            raise ValueError("A valid price is required for LIMIT orders.")
    return price

def validate_stop_price(order_type: OrderType, stop_price: Optional[float] = None) -> Optional[float]:
    if order_type == OrderType.STOP_MARKET:
        if stop_price is None or stop_price <= 0:
            raise ValueError("A valid stopPrice is required for STOP_MARKET orders.")
    return stop_price
