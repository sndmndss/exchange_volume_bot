import enum


class OrderType(enum.Enum):
    LIMIT = "Limit"


class Side(enum.Enum):
    BUY = "Bid"
    SELL = "Ask"


class Symbol(enum.Enum):
    pass


class TimeInForce(enum.Enum):
    GTC = "GTC"
    IOC = "IOC"
    FOK = "FOK"


class SelfTradePrevention(enum.Enum):
    ALLOW = "Allow"


class PostOnly(enum.Enum):
    FALSE = False
    TRUE = True


class Instruction(enum.Enum):
    ORDER_EXECUTE = "orderExecute"
