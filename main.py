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

    allied_forces = allied_unit_list[50:55]
    japan_forces = japan_unit_list[15:20]

    for unit in allied_forces:
        print(unit.unit_name)

    for unit in japan_forces:
        print(unit.unit_name)

    analyzer = BattleAnalyzer(intel_condition=enums.IntelCondition.INTERCEPT, reaction_player=enums.Player.ALLIES,
                              air_power_mod=enums.AirPowerModifier.Y1942, allied_ec_mod=0, japan_ec_mod=0)

    results = analyzer.analyze_battle(allied_forces, japan_forces)

    print(results)


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    print_hi()
