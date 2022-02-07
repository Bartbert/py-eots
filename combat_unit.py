import math
import enums


class CombatUnit:

    def __init__(self, nationality: str, unit_type: str, branch: str, attack_front: int, defense: int, attack_back: int,
                 move_range: int, move_range_extended: int, extended_limit: bool, unit_name: str, image_name_front: str,
                 image_name_back: str, id: int, is_flipped: bool = False, is_in_battle_hex: bool = False,
                 is_extended_range: bool = False, attack_modifier: int = 0):
        self.nationality = nationality
        self.unit_type = unit_type
        self.branch = branch
        self.attack_front = attack_front
        self.defense = defense
        self.attack_back = attack_back
        self.move_range = move_range
        self.move_range_extended = move_range_extended
        self.extended_limit = extended_limit
        self.unit_name = unit_name
        self.image_name_front = image_name_front
        self.image_name_back = image_name_back
        self.id = id
        self.is_flipped = is_flipped
        self.is_in_battle_hex = is_in_battle_hex
        self.is_extended_range = is_extended_range
        self.attack_modifier = attack_modifier

        if nationality == 'Japan':
            self.player = enums.Player.JAPAN
        else:
            self.player = enums.Player.ALLIES

    def combat_factors(self):

        combat_factors = self.attack_front

        if self.is_flipped:
            combat_factors = self.attack_back

        combat_factors += self.attack_modifier

        if self.is_extended_range:
            combat_factors = int(math.ceil(combat_factors / 2))

        return combat_factors
