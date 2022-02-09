import math
import pandas as pd
import enums
from itertools import product
from combat_unit import CombatUnit


def combat_result(die_roll: int, drm: int):
    modified_die_roll = die_roll + drm

    if modified_die_roll <= 2:
        result = 0.25
    elif (modified_die_roll > 2) & (modified_die_roll <= 5):
        result = 0.50
    else:
        result = 1.00

    return result


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

    def die_roll_modifier(self, player: enums.Player):
        drm = 0

        if player == enums.Player.ALLIES:
            drm += self.allied_ec_mod
            drm += self.air_power_mod

            if (self.intel_condition == enums.IntelCondition.SURPRISE) & (self.reaction_player != player):
                drm += 3
            elif (self.intel_condition == enums.IntelCondition.AMBUSH) & (self.reaction_player == player):
                drm += 4

        elif player == enums.Player.JAPAN:
            drm += self.japan_ec_mod

            if (self.intel_condition == enums.IntelCondition.SURPRISE) & (self.reaction_player != player):
                drm += 3

        return drm

    def analyze_battle(self, allied_forces: [CombatUnit], japan_forces: [CombatUnit]):
        dice_values = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
        die_combinations = product(dice_values, repeat=2)

        allied_die_rolls = []
        allied_results = []
        allied_losses = []

        japan_die_rolls = []
        japan_results = []
        japan_losses = []

        battle_results = []

        allied_forces_cf = sum(map(lambda x: x.combat_factors(), allied_forces))
        japan_forces_cf = sum(map(lambda x: x.combat_factors(), japan_forces))

        allied_drm = self.die_roll_modifier(enums.Player.ALLIES)
        japan_drm = self.die_roll_modifier(enums.Player.JAPAN)

        for die_roll in die_combinations:
            allied_die_roll = die_roll[0]
            japan_die_roll = die_roll[1]

            allied_result = combat_result(allied_die_roll, allied_drm)
            japan_result = combat_result(japan_die_roll, japan_drm)

            # The Combat Factor loss inflicted on the player's forces by his opponent
            # The actual Battle losses are determined based on damage allocation
            japan_loss_result = math.ceil(allied_forces_cf * allied_result)
            allied_loss_result = math.ceil(japan_forces_cf * japan_result)

            allied_die_rolls.append(allied_die_roll)
            allied_results.append(allied_result)
            allied_losses.append(allied_loss_result)

            japan_die_rolls.append(japan_die_roll)
            japan_results.append(japan_result)
            japan_losses.append(japan_loss_result)

        results_data = {
            'allied_die_roll': allied_die_rolls,
            'allied_result': allied_results,
            'allied_losses': allied_losses,
            'japan_die_roll': japan_die_rolls,
            'japan_result': japan_results,
            'japan_losses': japan_losses
        }

        return pd.DataFrame(data=results_data)

