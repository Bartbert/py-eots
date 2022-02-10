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


def select_unit_for_damage(combat_forces: [CombatUnit], damage_to_apply: int, critical_hit: bool,
                           enemy_air_unit_count: int):
    combat_forces.sort(key=lambda x: (-x.loss_delta(), x.defense))

    # Find the number of air units that have already received damage
    air_units_damaged = sum(
        1 for u in combat_forces if (u.move_range > 0) & (u.damage_flipped | u.damage_eliminated))

    for unit in combat_forces:

        # Skip this unit if the number of air units that have already received damage equals the
        # enemy_air_unit_count, and this is an air unit that has NOT yet received damage.
        if (air_units_damaged == enemy_air_unit_count) & (unit.damage_flipped is False) & (
                unit.damage_eliminated is False):
            next()

        if critical_hit:
            # Skip this unit if the damage_to_apply is less than the defense value of the unit
            if unit.defense > damage_to_apply:
                next()

            return unit

        else:
            # Skip this unit if the damage_to_apply is less than the defense value of the unit
            if unit.defense > damage_to_apply:
                next()

            # Skip this unit if the unit is flipped, and there are still other units that haven't been flipped
            unflipped_unit_count = sum(
                1 for u in combat_forces if (u.damage_flipped is False) & (u.is_flipped is False))

            if (unit.damage_flipped | unit.is_flipped) & (unflipped_unit_count > 0):
                next()

            return unit

    # If we get through the entire list without selecting a unit, then just return None
    return None


def apply_damage(total_losses: int, critical_hit, combat_forces, opponent_air_unit_count):
    damage_applied = 0
    damage_to_apply = total_losses
    allied_losses = total_losses

    while damage_applied < allied_losses:
        selected_unit = select_unit_for_damage(combat_forces, damage_to_apply, critical_hit,
                                               opponent_air_unit_count)

        if selected_unit is not None:
            damage_applied += selected_unit.defense
            damage_to_apply -= selected_unit.defense

            if selected_unit.is_flipped:
                selected_unit.damage_eliminated = True
            else:
                selected_unit.damage_flipped = True
        else:
            break

    # If this was a critical hit, and no units were selected for damage at all, then apply damage to
    # the unit with the smallest defense value
    if (damage_applied == 0) & critical_hit:
        combat_forces.sort(key=lambda x: (x.defense, -x.loss_delta()))
        selected_unit = combat_forces[0]

        damage_applied += selected_unit.defense
        damage_to_apply -= selected_unit.defense

        if selected_unit.is_flipped:
            selected_unit.damage_eliminated = True
        else:
            selected_unit.damage_flipped = True


def determine_battle_winner(allied_forces: [CombatUnit], japan_forces: [CombatUnit],
                            combat_results: pd.DataFrame):

    allied_air_unit_count = sum(1 for u in allied_forces if u.move_range > 0)
    japan_air_unit_count = sum(1 for u in japan_forces if u.move_range > 0)

    for row in combat_results:
        # Apply damage to Allied units
        allied_losses = row['allied_losses']
        critical_hit = row['japan_die_roll'] == 9

        apply_damage(allied_losses, critical_hit, allied_forces, japan_air_unit_count)

        # Apply damage to Japan units
        japan_losses = row['japan_losses']
        critical_hit = row['allied_die_roll'] == 9

        apply_damage(japan_losses, critical_hit, japan_forces, allied_air_unit_count)


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

        allied_forces_cf = sum(map(lambda x: x.combat_factor(), allied_forces))
        japan_forces_cf = sum(map(lambda x: x.combat_factor(), japan_forces))

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
