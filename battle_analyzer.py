import enums
from combat_unit import CombatUnit


class BattleAnalyzer:

    def __init__(self, intel_condition: enums.IntelCondition = enums.IntelCondition.INTERCEPT,
                 reaction_player: enums.Player = enums.Player.ALLIES,
                 air_power_mod: enums.AirPowerModifier = enums.AirPowerModifier.Y1942,
                 allied_ec_mod: int = 0, japan_ec_mod: int = 0) -> object:
        self.intel_condition = intel_condition
        self.reaction_player = reaction_player
        self.air_power_mod = air_power_mod
        self.allied_ec_mod = allied_ec_mod
        self.japan_ec_mod = japan_ec_mod

    def analyze_battle(self, allied_forces: [CombatUnit], japan_forces: [CombatUnit]):
        return allied_forces
