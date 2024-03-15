import asyncio

_lock = asyncio.Lock()
bid_price = 0.00
ask_price = 0.00
bias = 0.12


async def rise_bid_price(hard=False):
    global bid_price
    async with _lock:
        if not hard:
            bid_price = round(bid_price + bias, 2)
        else:
            bid_price = round(bid_price + (bias*20), 2)
    return bid_price


async def decrease_bid_price(hard=False):
    global bid_price
    async with _lock:
        if not hard:
            bid_price = round(bid_price - bias, 2)
        else:
            bid_price = round(bid_price - (bias*20))
    return bid_price


async def rise_ask_price(hard=False):
    global ask_price
    async with _lock:
        if not hard:
            ask_price = round(ask_price + bias, 2)
        else:
            ask_price = round(ask_price + (bias*20))
    return ask_price


async def decrease_ask_price(hard=False):
    global ask_price
    async with _lock:
        if not hard:
            ask_price = round(ask_price - bias, 2)
        else:
            ask_price = round(ask_price - (bias * 20), 2)
    return ask_price
