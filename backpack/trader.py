import aiohttp
from aiohttp.client_exceptions import ContentTypeError
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
import base64
import json
import requests
from loguru import logger
from enums.request_enums import *
from time import time
from utils.helpers import (random_quantity,
                           random_sleep_time,
                           middle_ask_price,
                           middle_bid_price)
import asyncio


async def _handle_post(self, params):
    """
        Asynchronously sends a POST request to the specified URL with the given parameters.

        Args:
            params (dict): The parameters to be sent in the POST request.

        Returns:
            dict or str: The JSON response as a dictionary if the content type is JSON, otherwise the response text.
        """
    async with aiohttp.ClientSession() as session:
        async with session.post("https://api.backpack.exchange/api/v1/order",
                                headers=(await self.headers(params=params,
                                                            instruction=Instruction.ORDER_EXECUTE.value)),
                                data=json.dumps(params), proxy=self.proxy) as response:
            try:
                return await response.json()
            except ContentTypeError:
                return await response.text()


class Site:
    """
        Represents a trading site with methods to interact with its API.

        Attributes:
            WINDOW (int): The time window for the signature validity.
            public_key (str): The public key for API access.
            private_key (Ed25519PrivateKey): The private key for signing requests.
            proxy (str): The proxy URL to be used for requests.
        """
    WINDOW = 5000

    def __init__(self, token, private_key, proxy):
        self.public_key = token
        self.private_key = self.private_key = Ed25519PrivateKey.from_private_bytes(
            base64.b64decode(private_key)
        )
        self.proxy = proxy

    async def headers(self, params: dict, instruction: str) -> dict:
        """
                Generates the headers required for a request, including the signature.

                Args:
                    params (dict): The parameters that will be included in the request.
                    instruction (str): The instruction to be included in the signature.

                Returns:
                    dict: The headers including the API key, signature, timestamp, and content type.
        """
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

    async def get_order_history(self, symbol):
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.backpack.exchange/api/v1/trades",
                                   headers=await self.headers({"symbol": symbol},
                                                              "fillHistoryQueryAll"),
                                   params={"symbol": symbol}, proxy=self.proxy) as response:
                try:
                    return await response.json()
                except ContentTypeError:
                    print(await response.text())

    async def get_user_order_history(self):
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.backpack.exchange/wapi/v1/history/fills",
                                   headers=await self.headers({"limit": 999},
                                                              "fillHistoryQueryAll"),
                                   params={"limit": 999}, proxy=self.proxy) as response:
                try:
                    return await response.json()
                except ContentTypeError:
                    logger.error("Backpack api is shit so try few more times")
                    return await response.text()



class Trade(Site):
    """
        Represents a trading operation, inheriting from the Site class.

        Attributes:
            public_key (str): The public key for API access.
            private_key (str): The private key for signing requests.
            quantity (float): The quantity to trade.
            symbol (str): The trading symbol.
            volume (float): The total volume traded.
            time_in_force (str): The time in force policy for the order.
            proxy (str): The proxy URL to be used for requests.
        """
    def __init__(self, public_key: str,
                 private_key: str,
                 min_quantity: float | int,
                 max_quantity: float | int,
                 symbol: str,
                 time_in_force: str,
                 proxy: str):

        super().__init__(public_key, private_key, proxy)
        self.quantity = random_quantity(min_quantity, max_quantity)
        self.symbol = symbol
        self.volume = 0
        self.time_in_force = time_in_force

    async def buy_order(self):
        """
                Asynchronously places a buy order at the middle bid price.

                Returns:
                    None: The function returns nothing but logs the outcome of the order.
        """
        price = await middle_bid_price(await self.get_order_history(self.symbol))
        params = {
            "orderType": OrderType.LIMIT.value,
            "price": str(price),
            "quantity": str(self.quantity),
            "side": Side.BUY.value,
            "symbol": self.symbol,
            "timeInForce": self.time_in_force,
            }
        r = await _handle_post(self=self, params=params)
        if isinstance(r, dict) and len(r) > 2:
            if r["status"] == "Expired":
                logger.warning(f"{r['orderType']} {r['side']} order for {r['quantity']} {r['symbol']} "
                               f"was not filled with price : {str(price)}")
                await asyncio.sleep(3)
                await self.buy_order()
            elif r["status"] == "Filled":
                logger.success(f"{r['orderType']} {r['side']} order for {r['quantity']} {r['symbol']} "
                               f"was filled with price : {str(price)}")
                self.volume += price * self.quantity
                logger.success(f"Current {self.public_key} account volume: {str(self.volume)}")
                await asyncio.sleep(random_sleep_time())
                await self._sell_order()
            elif r["status"] == "New":
                logger.success(f"{r['orderType']} {r['side']} order for {r['quantity']} {r['symbol']} "
                               f"was created with price : {str(price)}")
                await self._sell_order()
            else:
                logger.error("Unexpected responce"+str(r))
        elif len(r) < 2:
            logger.error("API is overloaded")
        else:
            if r == "Insufficient funds":
                logger.error("Insufficient funds, please change the quantity range")
            else:
                logger.error(f"{r}, check the quantity range and your account funds or contact developer")

    async def _sell_order(self):
        """
                Asynchronously places a sell order at the middle ask price.

                Returns:
                    None: The function returns nothing but logs the outcome of the order.
        """
        price = await middle_ask_price(await self.get_order_history(self.symbol))
        params = {
            "orderType": OrderType.LIMIT.value,
            "price": price,
            "quantity": str(self.quantity),
            "selfTradePrevention": SelfTradePrevention.ALLOW.value,
            "side": Side.SELL.value,
            "symbol": self.symbol,
            "timeInForce": self.time_in_force,
            }
        r = await _handle_post(self=self, params=params)
        if isinstance(r, dict) and len(r) > 2:
            if r["status"] == "Expired":
                logger.warning(f"{r['orderType']} {r['side']} order for {r['quantity']} {r['symbol']} "
                               f"was not filled with price : {str(price)}")
                await asyncio.sleep(3)
                await self._sell_order()
            elif r["status"] == "Filled":
                logger.success(f"{r['orderType']} {r['side']} order for {r['quantity']} {r['symbol']} "
                               f"was filled with ask_price: {str(price)}")
                self.volume += price * self.quantity
                logger.success(f"Current {self.public_key} account volume: {str(self.volume)}")
                await asyncio.sleep(random_sleep_time())
            elif r["status"] == "New":
                logger.success(f"{r['orderType']} {r['side']} order for {r['quantity']} {r['symbol']} "
                               f"was created with price : {str(price)}")
        elif len(r) < 2:
            logger.error("API is overloaded")
        else:
            logger.error(r + str(price) + str(params))
            self.quantity = round(self.quantity - 0.01, 2)
            await self._sell_order()