import aiohttp
from aiohttp.client_exceptions import ContentTypeError
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
import base64
import json
import requests
from enums.request_enums import *
from loguru import logger
from utils import balancer
from time import time
from utils.helpers import random_quantity, random_sleep_time
import asyncio


async def _handle_post(self, params):
    async with aiohttp.ClientSession() as session:
        async with session.post("https://api.backpack.exchange/api/v1/order",
                                headers=(await self.headers(params=params,
                                                            instruction=Instruction.ORDER_EXECUTE.value)),
                                data=json.dumps(params)) as response:
            try:
                return await response.json()
            except ContentTypeError:
                return await response.text()


class Site:
    WINDOW = 5000

    def __init__(self, token, private_key):
        self.public_key = token
        self.private_key = self.private_key = Ed25519PrivateKey.from_private_bytes(
            base64.b64decode(private_key)
        )

    async def headers(self, params: dict, instruction: str) -> dict:
        sign_str = f"instruction={instruction}" if instruction else ""
        sorted_params = "&".join(
            f"{key}={value}" for key, value in sorted(params.items())
        )
        if sorted_params:
            sign_str += "&" + sorted_params
        timestamp = int(time() * 1e3)
        sign_str += f"&timestamp={timestamp}&window={self.WINDOW}"
        signature_bytes = self.private_key.sign(sign_str.encode())
        encoded_signature = base64.b64encode(signature_bytes).decode()
        headers = {
            "X-API-Key": self.public_key,
            "X-Signature": encoded_signature,
            "X-Timestamp": str(timestamp),
            "X-Window": str(self.WINDOW),
            "Content-Type": "application/json; charset=utf-8",
        }
        return headers

    async def _sign(self, data):
        signature = self.private_key.sign(data.encode())
        signature_base64 = base64.b64encode(signature).decode()
        return str(signature_base64)

    @staticmethod
    def get_markets():
        response = requests.get("https://api.backpack.exchange/api/v1/markets")
        return response.json()


class Trade(Site):
    def __init__(self, public_key: str,
                 private_key: str,
                 min_quantity: float | int,
                 max_quantity: float | int,
                 symbol: str,
                 biased=False):

        super().__init__(public_key, private_key)
        self.quantity = random_quantity(min_quantity, max_quantity)
        self.symbol = symbol
        self.biased = biased

    async def buy_order(self):
        params = {
            "orderType": OrderType.LIMIT.value,
            "price": str(balancer.bid_price),
            "quantity": str(self.quantity),
            "side": Side.BUY.value,
            "symbol": self.symbol,
            "timeInForce": TimeInForce.IOC.value
            }
        r = await _handle_post(self=self, params=params)
        if isinstance(r, dict) and len(r) > 2:
            if r["status"] == "Expired":
                logger.warning(f"{r['orderType']} {r['side']} order for {r['quantity']} {r['symbol']} "
                               f"was not filled with price : {str(balancer.bid_price)}")
                await balancer.rise_bid_price()
                logger.info(f"Price was increased, current price :  {str(balancer.bid_price)}")
                await asyncio.sleep(3)
                await self.buy_order()
            elif r["status"] == "Filled":
                logger.success(f"{r['orderType']} {r['side']} order for {r['quantity']} {r['symbol']} "
                               f"was filled with price : {str(balancer.bid_price)}")
                await balancer.rise_ask_price(self.biased)
                await balancer.decrease_bid_price(self.biased)
                logger.success(f"Price was increased for ask and decreased for Bid, "
                               f"current price :  {str(balancer.bid_price)}")
                await asyncio.sleep(random_sleep_time())
                await self._sell_order()
            else:
                logger.error("Unexpected problem!")
        elif len(r) < 2:
            logger.error("API is overloaded")
        else:
            if r == "Insufficient funds":
                logger.error("Insufficient funds, please change the quantity range")
            else:
                logger.error(f"{r}, check the quantity range and your account funds or contact developer")

    async def _sell_order(self):
        params = {
            "orderType": OrderType.LIMIT.value,
            "price": str(balancer.ask_price),
            "quantity": str(self.quantity),
            "selfTradePrevention": SelfTradePrevention.ALLOW.value,
            "side": Side.SELL.value,
            "symbol": self.symbol,
            "timeInForce": TimeInForce.IOC.value,
            }
        r = await _handle_post(self=self, params=params)
        if isinstance(r, dict) and len(r) > 2:
            if r["status"] == "Expired":
                logger.warning(f"{r['orderType']} {r['side']} order for {r['quantity']} {r['symbol']} "
                               f"was not filled with price : {str(balancer.ask_price)}")
                await balancer.decrease_ask_price()
                logger.warning(f"Price was decreased by {balancer.bias}, current price :  {str(balancer.ask_price)}")
                await asyncio.sleep(3)
                await self._sell_order()
            elif r["status"] == "Filled":
                logger.success(f"{r['orderType']} {r['side']} order for {r['quantity']} {r['symbol']} "
                               f"was filled with ask_price: {str(balancer.ask_price)}")
                await balancer.rise_ask_price(self.biased)
                await balancer.decrease_bid_price(self.biased)
                logger.success(f"Price was increased by {balancer.bias}, current price :  {str(balancer.ask_price)}")
                await asyncio.sleep(random_sleep_time())
            else:
                logger.error("Unexpected problem!")
        elif len(r) < 2:
            logger.error("API is overloaded")
        else:
            logger.error(r)
