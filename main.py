import asyncio
from backpack.trader import Trade, Site
from utils.helpers import *
import sys
from enums.request_enums import TimeInForce


async def run_all(queue: list):
    """
    Asynchronously executes the 'buy_order' method for each trading bot instance in the queue.

    Args:
        queue (list): A list of trading bot instances to execute orders.

    Returns:
        None: The function returns nothing but awaits the completion of all tasks.
    """
    tasks = []
    for bot in queue:
        tasks.append(bot.buy_order())
    await asyncio.gather(*tasks)


async def infinite_run(public_keys, private_keys, min_quantity, max_quantity, symbol, time_in_force, proxies):
    """
    Continuously runs the trading bot with the given configuration until the process is interrupted.

    Args:
        public_keys (list): A list of public keys for the trading accounts.
        private_keys (list): A list of private keys for the trading accounts.
        min_quantity (str): The minimum quantity for the buy order.
        max_quantity (str): The maximum quantity for the buy order.
        symbol (str): The trading symbol for the buy order.
        time_in_force (str): The time in force policy for the buy order.
        proxies (list): A list of proxy servers to use for each trading bot instance.

    Returns:
        None: The function runs indefinitely and does not return a value.
    """
    while True:
        queue = []
        for y in range(len(public_keys)):
            trade_instance = (Trade(public_keys[y],
                                    private_keys[y],
                                    float(min_quantity),
                                    float(max_quantity),
                                    symbol,
                                    time_in_force,
                                    proxies[y])
                              )
            queue.append(trade_instance)
        await run_all(queue)


async def extra_options():
    """
    Provides additional options for the user to change configuration or check account volume.

    The function allows the user to change the sleep interval or check the account volume
    and spent fees from the last 999 filled orders. After completion, it restarts the main function.

    Returns:
        None: The function may exit the program or restart the main function based on user input.
    """

    print("1.Change random sleep time (default are 5:10)\n2.Check account volume and spent fees\n")
    extra_choice = input()
    if extra_choice.isdigit():
        if extra_choice == "1":
            min_sleep = input("minimal time in seconds: ")
            max_sleep = input("maximal time in seconds: ")
            try:
                sleep_minimal = int(min_sleep)
                sleep_maximal = int(max_sleep)
            except ValueError:
                print("Enter only numbers in seconds")
        elif extra_choice == "2":
            tasks = []
            proxies = proxy_formation()
            public_keys, private_keys = keys_loader()
            for iteration, public_key in enumerate(public_keys):
                tasks.append(Site(public_key,
                                  private_keys[iteration], proxies[iteration]).get_user_order_history())
            results = await asyncio.gather(*tasks)
            for iteration, result in enumerate(results):
                volume, fee = await account_volume(result)
                print(f"{public_keys[iteration]} volume: {volume}\n"
                      f"{public_keys[iteration]} fees: {fee}")

        await main()


async def main():
    """
        The main entry point of the trading bot application.

        This function presents the user with various options to configure the trading bot,
        such as selecting a trading symbol, contract format, and quantity spread. It also
        provides access to extra options for changing configuration or checking account volume.

        Returns:
            None: The function is the main event loop of the application and does not return a value.
        """
    order_types = ""
    for iteration, order in enumerate(TimeInForce):
        order_types += f"{iteration}.{order.name}\n"
    market = Site.get_markets()
    symbols, symbols_list = get_symbols(market)
    print(f"Choose symbol:\n" + symbols + "\nPrint 000 for extra-options")
    symbol_choice = input()
    if symbol_choice == "000":
        await extra_options()
        sys.exit()
    if symbol_choice.isdigit():
        if int(symbol_choice) <= len(symbols_list):
            print("Choose a contract format:\n" + order_types)
            order_type = input()
            try:
                print(f"Write the quantity spread for buying {symbols_list[int(symbol_choice)]}")
                min_quantity = input("Minimum: ")
                max_quantity = input("Maximum: ")
                try:
                    proxies = proxy_formation()
                    public_keys, private_keys = keys_loader()
                    if 0.01 <= float(min_quantity) < float(max_quantity):
                        if len(public_keys) == len(private_keys) == len(proxies):
                            await infinite_run(public_keys, private_keys,
                                               min_quantity, max_quantity,
                                               symbols_list[int(symbol_choice)],
                                               TimeInForce(int(order_type)).name,
                                               proxies,
                                               )
                        else:
                            print("Quantity of private_keys, public_keys and proxies must be equal!")
                except ValueError as e:
                    print(e)
            except ValueError:
                print("Write only number with dots, as: 100.50")
        else:
            print("Your number is out of range")
    else:
        print("The choice must be a number of symbol")


if __name__ == '__main__':
    asyncio.run(main())
