import random

# minimal sleep time between Bid and Ask orders
sleep_minimal = 5
sleep_maximal = 10


def get_symbols(market: dict) -> str and list:
    """
       Generates a string representation of market symbols and a list of symbols.

       Args:
           market (dict): A dictionary containing market data with symbol information.

       Returns:
           tuple: A tuple containing a string of enumerated symbols and a list of symbol strings.
       """
    symbols_list = [item['symbol'] for item in market]
    symbols = '\n'.join(f'{iteration} {symbol}' for iteration, symbol in enumerate(symbols_list))
    return symbols, symbols_list


def random_quantity(min_q: float, max_q: float) -> float:
    """
        Generates a random quantity within a specified range.

        Args:
            min_q (float): The minimum quantity value.
            max_q (float): The maximum quantity value.

        Returns:
            float: A random quantity rounded to 2 decimal places.
        """
    quantity = round(random.uniform(min_q, max_q), 2)
    return quantity


def proxy_formation() -> list:
    """
        Reads proxy information from a file and formats it into a list of proxy URLs.

        Returns:
            list: A list of formatted proxy URLs.
        """
    proxies = []
    with open("data/proxies.txt", "r") as f:
        for line in f:
            proxy_list = (line.rstrip().split(":"))
            proxies.append(f"http://{proxy_list[2]}:{proxy_list[3]}@{proxy_list[0]}:{proxy_list[1]}")
    return proxies


def keys_loader():
    """
       Loads public and private keys from files.

       Returns:
           tuple: A tuple containing two lists, one for public keys and one for private keys.
    """
    public_keys = []
    private_keys = []
    with open("data/public_keys.txt", "r") as f:
        for line in f:
            public_keys.append(line.rstrip())
    with open("data/private_keys.txt", "r") as f:
        for line in f:
            private_keys.append(line.rstrip())
    return public_keys, private_keys


def random_sleep_time():
    """
        Generates a random sleep time within a specified range.

        Returns:
            int: A random sleep time in seconds.
        """
    sleep_time = random.randint(sleep_minimal, sleep_maximal)
    return sleep_time


async def middle_bid_price(order_history) -> float:
    """
        Calculates the median bid price from order history.

        Args:
            order_history (list): A list of order history dictionaries.

        Returns:
            float: The median bid price.
        """
    prices = [float(item['price']) for item in order_history if not item['isBuyerMaker']]
    sorted_prices = sorted(prices)
    n = len(sorted_prices)
    if n % 2 == 1:
        median_price = round(sorted_prices[n//2], 2)
    else:
        median_price = round((sorted_prices[n//2-1]+sorted_prices[n//2]) / 2, 2)
    return median_price


async def middle_ask_price(order_history) -> float:
    """
        Calculates the median ask price from order history.

        Args:
            order_history (list): A list of order history dictionaries.

        Returns:
            float: The median ask price.
        """
    prices = [float(item['price']) for item in order_history if item['isBuyerMaker']]
    sorted_prices = sorted(prices)
    n = len(sorted_prices)
    if n % 2 == 1:
        median_price = round(sorted_prices[n//2], 2)
    else:
        median_price = round((sorted_prices[n//2-1]+sorted_prices[n//2]) / 2, 2)
    return median_price


async def account_volume(account_orders):
    """
        Calculates the total volume and fees from account orders.

        Args:
            account_orders (list): A list of account order dictionaries.

        Returns:
            tuple: A tuple containing the total volume and total fees.
        """
    prices = [float(item['price'])*float(item["quantity"]) for item in account_orders]
    fees = [float(item['price'])*float(item["fee"])
            if item["feeSymbol"] != 'USDC' else float(item["fee"]) for item in account_orders]
    return sum(prices), sum(fees)
