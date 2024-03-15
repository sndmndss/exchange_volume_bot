import random

sleep_minimal = 35
sleep_maximal = 95


def get_symbols(market: dict) -> str and list:
    symbols_list = [item['symbol'] for item in market]
    symbols = '\n'.join(f'{iteration} {symbol}' for iteration, symbol in enumerate(symbols_list))
    return symbols, symbols_list


def random_quantity(min_q: float, max_q: float) -> float:
    quantity = round(random.uniform(min_q, max_q), 2)
    return quantity


def proxy_formation() -> list:
    proxies = []
    with open("data/proxies.txt", "r") as f:
        for line in f:
            proxy_list = (line.rstrip().split(":"))
            proxies.append(f"http://{proxy_list[0]}:{proxy_list[1]}@{proxy_list[2]}:{proxy_list[3]}")
    return proxies


def keys_loader():
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
    sleep_time = random.randint(sleep_minimal, sleep_maximal)
    return sleep_time
