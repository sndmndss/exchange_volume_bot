import asyncio

_lock = asyncio.Lock()
price = 0


async def rise_price():
    global price
    async with _lock:
        price += 1
    return price


async def decrease_price():
    global price
    async with _lock:
        price -= 1
    return price
