import time
import hmac
import hashlib
import requests
from urllib.parse import urlencode
from bot.logging_config import logger

class BinanceFuturesClient:
    BASE_URL = "https://testnet.binancefuture.com"

    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.session = requests.Session()
        self.session.headers.update({
            "X-MBX-APIKEY": self.api_key,
            "Content-Type": "application/x-www-form-urlencoded"
        })
        logger.info("Initialized BinanceFuturesClient for Testnet")

    def _generate_signature(self, query_string: str) -> str:
        """Generate HMAC SHA256 signature for Binance API."""
        return hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

    def _send_request(self, method: str, endpoint: str, payload: dict = None) -> dict:
        """Internal method to dispatch signed HTTP requests."""
        if not payload:
            payload = {}
        
        # Add mandatory timestamp
        payload['timestamp'] = int(time.time() * 1000)
        
        # We need to compute query string to sign
        query_string = urlencode(payload, doseq=True)
        signature = self._generate_signature(query_string)
        
        # Add signature to payload
        payload['signature'] = signature
        # Re-encode with signature for the actual body/url
        encoded_payload = urlencode(payload, doseq=True)
        url = f"{self.BASE_URL}{endpoint}"

        logger.debug(f"Sending {method} request to {url}")
        logger.debug(f"Request Payload: {payload}")

        try:
            if method == "GET":
                response = self.session.get(url, params=payload)
            elif method == "POST":
                # For POST requests, parameters are sent in the body usually or as query.
                # Binance Futures POST endpoints typically accept query params OR urlencoded body.
                response = self.session.post(url, data=encoded_payload)
            elif method == "DELETE":
                response = self.session.delete(url, data=encoded_payload)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()
            response_json = response.json()
            logger.debug(f"Response Body: {response_json}")
            return response_json

        except requests.exceptions.HTTPError as err:
            logger.error(f"HTTPError: {err}")
            # Try to parse Binance error code
            try:
                error_body = err.response.json()
                logger.error(f"Binance API Error: {error_body}")
                raise Exception(f"Binance API Error [{error_body.get('code')}]: {error_body.get('msg')}")
            except Exception as e:
                # If we couldn't parse JSON, just raise the original generic exception
                if "Binance API Error" not in str(e):
                    raise Exception(f"HTTP Error: {err.response.text}")
                raise e
        except requests.exceptions.RequestException as err:
            logger.error(f"RequestException (Network issue): {err}")
            raise Exception("Network error occurred while connecting to Binance API.")
