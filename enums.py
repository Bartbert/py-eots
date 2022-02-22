from enum import Enum
from enum import IntEnum


class IntelCondition(Enum):
    INTERCEPT = 0
    SURPRISE = 3
    AMBUSH = 4


class Player(Enum):
    ALLIES = 1
    JAPAN = 2
    UNKNOWN = 3


class AirPowerModifier(IntEnum):
    Y1942 = 0
    Y1943 = 1
    Y1944 = 3


class UnitType(Enum):
    AIR = 1
    NAVAL = 2
    GROUND = 3


class Branch(Enum):
    ARMY = 1
    NAVY = 2


class DeckType(Enum):
    FULL_DECK = 1
    SOUTH_PACIFIC = 2
