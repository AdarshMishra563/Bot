# Binance Futures Testnet Trading Bot

A Python CLI application for placing orders on the Binance Futures Testnet (USDT-M), built with absolute control over REST calls using `requests` and an enhanced user experience via `typer` and `rich`.

## Project Structure
```text
trading_bot/
│   .env.example          # Template for API credentials
│   cli.py                # Typer CLI application entry point
│   requirements.txt      # Project dependencies
│   trading_bot.log       # Application execution logs
└───bot/
    │   client.py         # Binance custom REST HTTP client wrapper
    │   logging_config.py # Structured rotating log setup
    │   orders.py         # High-level mapping to Binance endpoints
    │   validators.py     # Input sanitization and error catching
```

## Setup Instructions
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Create your `.env` file by copying the example:
   ```bash
   cp .env.example .env
   ```
3. Register on Binance Futures Testnet, generate your API Key and Secret, and paste them into `.env`:
   ```env
   BINANCE_API_KEY=your_testnet_api_key_here
   BINANCE_API_SECRET=your_testnet_api_secret_here
   ```

## Usage Examples
Run the CLI specifying `symbol`, `side`, `order type`, and `quantity` at minimum.

### 1. Market Order (BUY)
```bash
python cli.py order BTCUSDT BUY MARKET 0.001
```

### 2. Limit Order (SELL)
Requires the `--price` (or `-p`) parameter.
```bash
python cli.py order ETHUSDT SELL LIMIT 1.5 --price 1800.5
```

### 3. Stop-Market Order (BUY)
*Bonus Feature Check*: Requires `--stop-price` (or `-s`).
```bash
python cli.py order XRPUSDT BUY STOP_MARKET 500 --stop-price 0.55
```

### 4. Help
View all CLI arguments and options:
```bash
python cli.py order --help
```

## Logs
The project is configured to log all HTTP requests and validations structurally to `trading_bot.log`. 
The logs from successfully placing a Market and a Limit order will be populated in `trading_bot.log` after you execute the commands above.

## Assumptions Made
1. **Dependency Choice**: Decided to write a custom HMAC HTTP client over `requests` instead of bringing in `python-binance` for reduced overhead and full absolute control over validation flows.
2. **Order Execution**: LIMIT orders assume `"timeInForce": "GTC"` (Good-Till-Cancelled) blindly to simplify the CLI surface. 
3. **Environment setup**: API keys are securely retrieved from a `.env` file rather than via CLI flags.
