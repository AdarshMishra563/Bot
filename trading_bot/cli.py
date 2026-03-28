import os
import sys
import typer
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich import print as rprint
from dotenv import load_dotenv

from bot.client import BinanceFuturesClient
from bot.orders import place_order
from bot.validators import (
    validate_symbol, validate_quantity, validate_price, 
    validate_stop_price, OrderSide, OrderType
)
from bot.logging_config import logger

# Load environment variables from .env
load_dotenv()

app = typer.Typer(help="Binance Futures Testnet Trading Bot CLI")
console = Console()

@app.command()
def order(
    symbol: str = typer.Argument(..., help="Trading symbol, e.g., BTCUSDT"),
    side: OrderSide = typer.Argument(..., help="Order side: BUY or SELL"),
    order_type: OrderType = typer.Argument(..., help="Order type: MARKET, LIMIT, or STOP_MARKET"),
    quantity: float = typer.Argument(..., help="Quantity to trade"),
    price: Optional[float] = typer.Option(None, "--price", "-p", help="Price (Required for LIMIT orders)"),
    stop_price: Optional[float] = typer.Option(None, "--stop-price", "-s", help="Stop Price (Required for STOP_MARKET orders)")
):
    """
    Place an order on the Binance Futures Testnet.
    """
    try:
        # 1. Validation
        valid_symbol = validate_symbol(symbol)
        valid_quantity = validate_quantity(quantity)
        valid_price = validate_price(order_type, price)
        valid_stop_price = validate_stop_price(order_type, stop_price)

        # 2. Setup Client
        api_key = os.getenv("BINANCE_API_KEY")
        api_secret = os.getenv("BINANCE_API_SECRET")

        if not api_key or not api_secret:
            console.print("[bold red]Error[/bold red]: BINANCE_API_KEY and BINANCE_API_SECRET must be set in the .env file.")
            sys.exit(1)

        client = BinanceFuturesClient(api_key=api_key, api_secret=api_secret)

        # 3. Print Request Summary
        console.print(f"\\n[cyan]Submitting Order Request...[/cyan]")
        req_table = Table(show_header=False, box=None)
        req_table.add_row("Symbol:", valid_symbol)
        req_table.add_row("Side:", side.value)
        req_table.add_row("Order Type:", order_type.value)
        req_table.add_row("Quantity:", str(valid_quantity))
        if valid_price:
            req_table.add_row("Price:", str(valid_price))
        if valid_stop_price:
            req_table.add_row("Stop Price:", str(valid_stop_price))
        console.print(req_table)
        console.print("")

        # 4. Place Order via API
        response = place_order(
            client=client,
            symbol=valid_symbol,
            side=side.value,
            order_type=order_type.value,
            quantity=valid_quantity,
            price=valid_price,
            stop_price=valid_stop_price
        )

        # 5. Print Response Details
        console.print("[bold green]Success![/bold green] Order placed successfully.\\n")
        
        res_table = Table(title="Order Details")
        res_table.add_column("Field", style="cyan")
        res_table.add_column("Value", style="magenta")

        # Safely extract response fields
        res_table.add_row("Order ID", str(response.get("orderId", "N/A")))
        res_table.add_row("Status", str(response.get("status", "N/A")))
        res_table.add_row("Executed Qty", str(response.get("executedQty", "N/A")))
        res_table.add_row("Average Price", str(response.get("avgPrice", "N/A")))
        res_table.add_row("Type", str(response.get("type", "N/A")))
        res_table.add_row("Side", str(response.get("side", "N/A")))
        
        if response.get("price") and float(response.get("price")) > 0:
            res_table.add_row("Input Price", str(response.get("price")))
        if response.get("stopPrice") and float(response.get("stopPrice")) > 0:
            res_table.add_row("Stop Price", str(response.get("stopPrice")))

        console.print(res_table)

    except ValueError as ve:
        console.print(f"[bold red]Validation Error[/bold red]: {ve}")
        logger.error(f"Validation Error: {ve}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[bold red]API/Network Error[/bold red]: {e}")
        logger.error(f"API/Network Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    app()
