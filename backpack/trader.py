import aiohttp
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
import base64
import json
from enums.request_enums import *
from loguru import logger
from utils import balancer


async def _handle_post(headers, body):
    async with aiohttp.ClientSession() as session:
        async with session.post("https://api.backpack.exchange/api/v1/order",
                                headers=headers, data=body) as response:
            return await response.json()


class Site:
    WINDOW = 6000

    def __init__(self, token, private_key):
        self.public_key = token
        self.private_key = private_key

    async def headers(self, params: dict, instruction: str) -> dict:
        timestamp = await self._unix_time()
        params["window"] = self.WINDOW
        params["timestamp"] = timestamp
        sorted_params = sorted(params.items())
        query_string = f"instruction={instruction}&"+'&'.join(f"{key}={value}" for key, value in sorted_params)
        signature = await self._sign(query_string)
        headers = {
            'X-Timestamp': str(timestamp),
            'X-Window': str(self.WINDOW),
            'X-API-Key': self.public_key,
            'X-Signature': signature
        }
        return headers

    async def _sign(self, data):
        private_key_bytes = base64.b64decode(self.private_key)
        private_key = Ed25519PrivateKey.from_private_bytes(private_key_bytes)
        signature = private_key.sign(data.encode())
        signature_base64 = base64.b64encode(signature).decode()
        return signature_base64

    @staticmethod
    async def _unix_time():
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.backpack.exchange/api/v1/time") as response:
                return await response.text()


class Trade(Site):
    def __init__(self, public_key: str, private_key: str, quantity: int):
        super().__init__(public_key, private_key)
        self.price = balancer.price
        self.quantity = quantity

    async def buy_order(self):
        params = {
            "orderType": OrderType.LIMIT.value,
            "postOnly": PostOnly.FALSE.value,
            "price": self.price,
            "quantity": self.quantity,
            "selfTradePrevention": SelfTradePrevention.ALLOW.value,
            "side": Side.BUY.value,
            "symbol": Symbol.SOL.value,
            "timeInForce": TimeInForce.IOC.value,
            }
        headers = await self.headers(params=params, instruction=Instruction.ORDER_EXECUTE.value)
        headers['Content-Type'] = 'application/json; charset=utf-8'
        body = json.dumps(params)
        r = await _handle_post(headers=headers, body=body)
        if r["status"] == "Cancelled":
            self.price = balancer.rise_price()
            logger.warning("Price was raised by 1 _, current price : " + str(self.price))
        elif r["status"] == "success":
            logger.success("Buy order was successfully processed with price : " + str(self.price))
        else:
            logger.error("Unexpected problem!")

    async def sell_order(self):
        params = {
            "orderType": OrderType.LIMIT.value,
            "postOnly": PostOnly.FALSE.value,
            "price": self.price,
            "quantity": self.quantity,
            "selfTradePrevention": SelfTradePrevention.ALLOW.value,
            "side": Side.SELL.value,
            "symbol": Symbol.SOL.value,
            "timeInForce": TimeInForce.IOC.value,
            }
        headers = await self.headers(params=params, instruction=Instruction.ORDER_EXECUTE.value)
        headers['Content-Type'] = 'application/json; charset=utf-8'
        body = json.dumps(params)
        r = await _handle_post(headers=headers, body=body)
        if r["status"] == "canceled":
            self.price = balancer.decrease_price()
            logger.warning("Price was decreased by 1 _, current price : " + str(self.price))
        elif r["status"] == "success":
            logger.success("Sell order was successfully processed with price : " + str(self.price))
        else:
            logger.error("Unexpected problem!")

    # async def get_markets(self):
    #     async with aiohttp.ClientSession() as session:
    #         async with session.get("https://api.backpack.exchange/api/v1/markets") as response:
    #             return await response.text()
