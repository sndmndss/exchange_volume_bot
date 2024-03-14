import asyncio
from backpack.trader import Trade
public_key = ""
private_key = ""


def main():
    print(asyncio.run(Trade(public_key, private_key).buy_order()))


if __name__ == '__main__':
    main()
