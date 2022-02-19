import math
import pandas as pd
import enums
import copy
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
    combat_forces.sort(key=lambda x: (x.defense, -x.loss_delta()))

    # Find the number of air units that have already received damage
    air_units_damaged = sum(
        1 for u in combat_forces if (u.move_range > 0) & (u.damage_flipped | u.damage_eliminated))

    for unit in combat_forces:

        # Skip this unit if it has already been eliminated
        if unit.damage_eliminated:
            continue

        # Skip this unit if the number of air units that have already received damage equals the
        # enemy_air_unit_count, and this is an air unit that has NOT yet received damage.
        if (unit.move_range > 0) & (air_units_damaged == enemy_air_unit_count) & \
                (not unit.damage_flipped) & (not unit.damage_eliminated):
            continue

        if critical_hit:
            # Skip this unit if the damage_to_apply is less than the defense value of the unit
            if unit.defense > damage_to_apply:
                continue

            return unit

        else:
            # Skip this unit if the damage_to_apply is less than the defense value of the unit
            if unit.defense > damage_to_apply:
                continue

            # Skip this unit if the unit is flipped, and there are still other units that haven't been flipped
            unflipped_unit_count = sum(
                1 for u in combat_forces if (not u.damage_flipped) & (not u.is_flipped))

            if (unit.damage_flipped | unit.is_flipped) & (unflipped_unit_count > 0):
                continue

            return unit

    # If we get through the entire list without selecting a unit, then just return None
    return None


def apply_damage(total_losses: int, critical_hit, combat_forces, opponent_air_unit_count):
    damage_applied = 0
    damage_to_apply = total_losses

    while damage_applied < total_losses:

        selected_unit = select_unit_for_damage(combat_forces, damage_to_apply, critical_hit, opponent_air_unit_count)

        if selected_unit is not None:
            damage_applied += selected_unit.defense
            damage_to_apply -= selected_unit.defense
            print(f'Critical Hit: {critical_hit}')
            print(f'Total Losses: {total_losses}')
            print(f'Selected unit: {selected_unit.unit_name}')
            print(f'Damage applied: {damage_applied}')
            print(f'Damage remaining to apply: {damage_to_apply}')
            print('============================================')

            if selected_unit.is_flipped | selected_unit.damage_flipped:
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


def determine_battle_winner(allied_forces: [CombatUnit], japan_forces: [CombatUnit], combat_results: pd.DataFrame,
                            intel_condition: enums.IntelCondition, reaction_player: enums.Player):
    allied_air_unit_count = sum(1 for u in allied_forces if u.move_range > 0)
    japan_air_unit_count = sum(1 for u in japan_forces if u.move_range > 0)

    for row in combat_results.iterrows():

        # Apply damage to Allied units
        allied_losses = row[1]['allied_losses']
        allied_critical_hit = row[1]['japan_die_roll'] == 9
        allied_result = row[1]['allied_result']

        allied_combat_forces = copy.deepcopy(allied_forces)

        apply_damage(allied_losses, allied_critical_hit, allied_combat_forces, japan_air_unit_count)

        allied_damage_applied = sum(map(lambda x: x.damage_applied(), allied_combat_forces))
        allied_remaining_cf = sum(map(lambda x: x.combat_factor(), allied_combat_forces))

        # Apply damage to Japan units
        japan_losses = row[1]['japan_losses']
        japan_critical_hit = row[1]['allied_die_roll'] == 9
        japan_result = row[1]['japan_result']

        japan_combat_forces = copy.deepcopy(japan_forces)

        apply_damage(japan_losses, japan_critical_hit, japan_combat_forces, allied_air_unit_count)

        japan_damage_applied = sum(map(lambda x: x.damage_applied(), japan_combat_forces))
        japan_remaining_cf = sum(map(lambda x: x.combat_factor(), japan_combat_forces))

        if (intel_condition == enums.IntelCondition.SURPRISE) & (reaction_player == enums.Player.ALLIES):

            # Recalculate Japan's losses using the remaining Allied forces
            japan_losses = int(math.ceil(allied_remaining_cf * allied_result))
            japan_combat_forces = copy.deepcopy(japan_forces)
            allied_air_unit_count = sum(
                1 for u in allied_combat_forces if (u.move_range > 0) & (not u.damage_eliminated))
            apply_damage(japan_losses, japan_critical_hit, japan_combat_forces, allied_air_unit_count)

            japan_damage_applied = sum(map(lambda x: x.damage_applied(), japan_combat_forces))
            japan_remaining_cf = sum(map(lambda x: x.combat_factor(), japan_combat_forces))

        elif ((intel_condition == enums.IntelCondition.SURPRISE) & (reaction_player == enums.Player.ALLIES) | (
                intel_condition == enums.IntelCondition.AMBUSH)):

            # Recalculate Allies losses using the remaining Japan forces
            allied_losses = int(math.ceil(japan_remaining_cf * japan_result))
            allied_combat_forces = copy.deepcopy(allied_forces)
            japan_air_unit_count = sum(1 for u in japan_combat_forces if (u.move_range > 0) & (not u.damage_eliminated))
            apply_damage(allied_losses, allied_critical_hit, allied_combat_forces, japan_air_unit_count)

            allied_damage_applied = sum(map(lambda x: x.damage_applied(), allied_combat_forces))
            allied_remaining_cf = sum(map(lambda x: x.combat_factor(), allied_combat_forces))

        combat_results.loc[row[0], 'allied_damage_applied'] = allied_damage_applied
        combat_results.loc[row[0], 'allied_remaining_cf'] = allied_remaining_cf
        combat_results.loc[row[0], 'allied_losses'] = allied_losses

        combat_results.loc[row[0], 'japan_damage_applied'] = japan_damage_applied
        combat_results.loc[row[0], 'japan_remaining_cf'] = japan_remaining_cf
        combat_results.loc[row[0], 'japan_losses'] = japan_losses

        allied_surviving_unit_count = sum(1 for u in allied_combat_forces if (not u.damage_eliminated))
        japan_surviving_unit_count = sum(1 for u in japan_combat_forces if (not u.damage_eliminated))

        allied_surviving_air_count = sum(
            1 for u in allied_combat_forces if (u.move_range > 0) & (not u.damage_eliminated))
        japan_surviving_air_count = sum(
            1 for u in japan_combat_forces if (u.move_range > 0) & (not u.damage_eliminated))

        if (allied_surviving_unit_count == 0) & (japan_surviving_unit_count == 0):
            # Offensive player wins if neither side has any surviving units
            if reaction_player == enums.Player.ALLIES:
                combat_results.loc[row[0], 'battle_winner'] = enums.Player.JAPAN.name
            else:
                combat_results.loc[row[0], 'battle_winner'] = enums.Player.ALLIES.name
        elif (allied_surviving_air_count == 0) & (japan_surviving_air_count > 0) & (
                reaction_player == enums.Player.JAPAN):
            # Reaction player wins if the Offensive player has no Air capable unit but the Reaction player does
            combat_results.loc[row[0], 'battle_winner'] = enums.Player.JAPAN.name
        elif (japan_surviving_air_count == 0) & (allied_surviving_air_count > 0) & (
                reaction_player == enums.Player.ALLIES):
            # Reaction player wins if the Offensive player has no Air capable unit but the Reaction player does
            combat_results.loc[row[0], 'battle_winner'] = enums.Player.ALLIES.name
        elif allied_remaining_cf == japan_remaining_cf:
            # Reaction player wins ties
            if reaction_player == enums.Player.ALLIES:
                combat_results.loc[row[0], 'battle_winner'] = enums.Player.ALLIES.name
            else:
                combat_results.loc[row[0], 'battle_winner'] = enums.Player.JAPAN.name
        else:
            if allied_remaining_cf > japan_remaining_cf:
                combat_results.loc[row[0], 'battle_winner'] = enums.Player.ALLIES.name
            elif japan_remaining_cf > allied_remaining_cf:
                combat_results.loc[row[0], 'battle_winner'] = enums.Player.JAPAN.name


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
            'allied_damage_applied': 0,
            'allied_remaining_cf': 0,
            'japan_die_roll': japan_die_rolls,
            'japan_result': japan_results,
            'japan_losses': japan_losses,
            'japan_damage_applied': 0,
            'japan_remaining_cf': 0,
            'battle_winner': enums.Player.UNKNOWN
        }

        combat_results = pd.DataFrame(data=results_data)

        determine_battle_winner(allied_forces, japan_forces, combat_results, intel_condition=self.intel_condition,
                                reaction_player=self.reaction_player)

        return combat_results
