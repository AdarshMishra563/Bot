from typing import Optional
from bot.client import BinanceFuturesClient
from bot.logging_config import logger

def place_order(
    client: BinanceFuturesClient,
    symbol: str,
    side: str,
    order_type: str,
    quantity: float,
    price: Optional[float] = None,
    stop_price: Optional[float] = None
) -> dict:
    """
    Common order placement wrapper.
    https://binance-docs.github.io/apidocs/futures/en/#new-order-trade
    """
    endpoint = "/fapi/v1/order"
    
    payload = {
        "symbol": symbol,
        "side": side,
        "type": order_type,
        "quantity": str(quantity),  # Binance accepts string floats usually
    }
    
    if order_type == "LIMIT":
        payload["price"] = str(price)
        payload["timeInForce"] = "GTC"  # Good Till Cancel required for LIMIT
    
    if order_type == "STOP_MARKET":
        payload["stopPrice"] = str(stop_price)
        payload["closePosition"] = "false"  # Explicit default, we are not making it close-only for now

    logger.info(f"Placing {order_type} {side} order for {quantity} {symbol}")
    
    try:
        response = client._send_request("POST", endpoint, payload)
        logger.info(f"Order successful! Order ID: {response.get('orderId')}")
        return response
    except Exception as e:
        logger.error(f"Failed to place order: {e}")
        raise
