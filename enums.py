from enum import Enum
from enum import IntEnum


class IntelCondition(Enum):
    INTERCEPT = 1
    SURPRISE = 2
    AMBUSH = 3


class Player(Enum):
    JAPAN = 1
    ALLIES = 2


class AirPowerModifier(IntEnum):
    Y1942 = 0
    Y1943 = 1
    Y1944 = 3
