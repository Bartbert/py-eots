import pandas as pd
from combat_unit import CombatUnit
from battle_analyzer import BattleAnalyzer
import enums


def print_hi():
    units = pd.read_csv('data/unit_data.csv')
    units['id'] = units.index

    an_units = units.loc[units['unit_type'] != 'Ground']

    allied_units = an_units.loc[an_units['nationality'] != 'Japan']
    japan_units = an_units.loc[an_units['nationality'] == 'Japan']

    allied_unit_list = [CombatUnit(**kwargs) for kwargs in allied_units.to_dict(orient='records')]
    japan_unit_list = [CombatUnit(**kwargs) for kwargs in japan_units.to_dict(orient='records')]

    allied_forces = allied_unit_list[60:65]
    allied_forces[0].is_flipped = True

    japan_forces = japan_unit_list[23:28]
    japan_forces[3].is_flipped = True

    for unit in allied_forces:
        print(f'Unit: {unit.unit_name}, Front: {unit.attack_front}, Back: {unit.attack_back}, CF: {unit.combat_factors()}')

    allied_forces_cf = sum(map(lambda x: x.combat_factors(), allied_forces))
    print(f'Allied CF Total: {allied_forces_cf}')

    for unit in japan_forces:
        print(f'Unit: {unit.unit_name}, Front: {unit.attack_front}, Back: {unit.attack_back}, CF: {unit.combat_factors()}')

    japan_forces_cf = sum(map(lambda x: x.combat_factors(), japan_forces))
    print(f'Japan CF Total: {japan_forces_cf}')

    analyzer = BattleAnalyzer(intel_condition=enums.IntelCondition.INTERCEPT, reaction_player=enums.Player.ALLIES,
                              air_power_mod=enums.AirPowerModifier.Y1942, allied_ec_mod=0, japan_ec_mod=0)

    results = analyzer.analyze_battle(allied_forces, japan_forces)

    print(results)


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    print_hi()
