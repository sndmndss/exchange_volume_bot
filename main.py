import asyncio
from backpack.trader import Trade, Site
from utils import balancer
from utils.helpers import *
import sys


async def run_all(queue):
    tasks = []
    for bot in queue:
        tasks.append(bot.buy_order())
    results = await asyncio.gather(*tasks)
    return results


def extra_options():
    print("1.Change bias\n"
          "2.Change minimal and maximal random sleep time between selling and buying\n")
    extra_choice = input()
    if extra_choice.isdigit():
        if extra_choice == "1":
            bias = input("Enter bias in float format : ")
            try:
                balancer.bias = float(bias)
            except ValueError:
                print("Float format!")
        elif extra_choice == "2":
            min_sleep = input("minimal time in seconds: ")
            max_sleep = input("maximal time in seconds: ")
            try:
                sleep_minimal = int(min_sleep)
                sleep_maximal = int(max_sleep)
            except ValueError:
                print("Enter only numbers in seconds")
        main()


async def main():
    queue = []
    market = Site.get_markets()
    symbols, symbols_list = get_symbols(market)
    print(f"Choose symbol:\n" + symbols + "\nPrint 000 for extra-options")
    symbol_choice = input()
    if symbol_choice == "000":
        extra_options()
        sys.exit()
    if symbol_choice.isdigit():
        if int(symbol_choice) <= len(symbols_list):
            print("Choose the first price for first Bid order\n"
                  "Then price will be calibrated by trying to increase or decrease price \n"
                  "using IOC order instruction that return the order if it was not satisfied immediately")
            print("Price: ")
            price = input()
            try:
                balancer.bid_price = float(price)
                balancer.ask_price = float(price)
                print(f"Write the quantity spread for buying {symbols_list[int(symbol_choice)]}")
                min_quantity = input("Minimum: ")
                max_quantity = input("Maximum: ")
                try:
                    proxies = proxy_formation()
                    public_keys, private_keys = keys_loader()
                    if 0.01 <= float(min_quantity) < float(max_quantity):
                        if len(public_keys) == len(private_keys) == len(proxies):
                            circles = int(input("How much circles all accounts supposed to have"))
                            queue = [[] for _ in range(circles)]
                            for i in range(circles):
                                for y in range(len(public_keys)):
                                    trade_instance = (Trade(public_keys[y],
                                                          private_keys[y],
                                                          float(min_quantity),
                                                          float(max_quantity),
                                                          symbols_list[int(symbol_choice)],
                                                          True
                                                          )
                                                    )
                                    queue[i].append(trade_instance)
                except ValueError:
                    print("Write only number with dots, as: 100.50")
            except ValueError:
                print("Write only number with dots, as: 100.50")

        else:
            print("Your number is out of range")
    else:
        print("The choice must be a number of symbol")
    for circle in queue:
        await run_all(circle)
        await asyncio.sleep(45)


if __name__ == '__main__':
    asyncio.run(main())
