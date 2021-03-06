import pandas as pd
from pprint import pprint
from IPython.display import display
from combat_unit import CombatUnit
from battle_analyzer import BattleAnalyzer
from battle_analyzer import apply_damage
import enums


def print_hi():
    units = pd.read_csv('data/unit_data.csv')
    units['unit_id'] = units.index

    an_units = units.loc[units['unit_type'] != 'Ground']

    allied_units = an_units.loc[an_units['nationality'] != 'Japan']
    japan_units = an_units.loc[an_units['nationality'] == 'Japan']

    allied_unit_list = [CombatUnit(**kwargs) for kwargs in allied_units.to_dict(orient='records')]
    japan_unit_list = [CombatUnit(**kwargs) for kwargs in japan_units.to_dict(orient='records')]

    allied_forces = allied_unit_list[50:55]
    allied_forces[0].is_flipped = True

    japan_forces = japan_unit_list[23:28]
    japan_forces[3].is_flipped = True

    allied_forces.sort(key=lambda x: (-x.loss_delta(), x.defense))

    for unit in allied_forces:
        print(
            f'Unit: {unit.unit_name}, Front: {unit.attack_front}, Back: {unit.attack_back}, Defense: {unit.defense}, '
            f'CF: {unit.combat_factor()}, Loss Delta: {unit.loss_delta()}, Range: {unit.move_range}')

    allied_forces_cf = sum(map(lambda x: x.combat_factor(), allied_forces))
    print(f'Allied CF Total: {allied_forces_cf}')

    for unit in japan_forces:
        print(
            f'Unit: {unit.unit_name}, Front: {unit.attack_front}, Back: {unit.attack_back}, CF: {unit.combat_factor()}')

    japan_forces_cf = sum(map(lambda x: x.combat_factor(), japan_forces))
    print(f'Japan CF Total: {japan_forces_cf}')

    analyzer = BattleAnalyzer(intel_condition=enums.IntelCondition.SURPRISE, reaction_player=enums.Player.ALLIES,
                              air_power_mod=enums.AirPowerModifier.Y1942, allied_ec_mod=0, japan_ec_mod=0)

    results = analyzer.analyze_battle(allied_forces, japan_forces)

    display(results)

    results_summary = results.groupby(by=['allied_result', 'allied_losses', 'japan_result', 'japan_losses'],
                                      as_index=False).agg(
        probability=pd.NamedAgg(column='allied_result', aggfunc='count'))
    print(results_summary)

    # apply_damage(total_losses=45, critical_hit=True, combat_forces=allied_forces, opponent_air_unit_count=5)


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    print_hi()
