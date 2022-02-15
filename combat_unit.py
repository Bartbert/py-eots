import math
import enums


class CombatUnit:

    def __init__(self, nationality: str, unit_type: str, branch: str, attack_front: int, defense: int, attack_back: int,
                 move_range: int, move_range_extended: int, extended_limit: bool, unit_name: str, image_name_front: str,
                 image_name_back: str, unit_id: int, is_flipped: bool = False, is_in_battle_hex: bool = False,
                 is_extended_range: bool = False, attack_modifier: int = 0):
        self.nationality = nationality

        if unit_type == 'Air':
            self.unit_type = enums.UnitType.AIR
        elif unit_type == 'Naval':
            self.unit_type = enums.UnitType.NAVAL
        else:
            self.unit_type = enums.UnitType.GROUND

        if branch == 'Army':
            self.branch = enums.Branch.ARMY
        else:
            self.branch = enums.Branch.NAVY

        self.attack_front = attack_front
        self.defense = defense
        self.attack_back = attack_back
        self.move_range = move_range
        self.move_range_extended = move_range_extended
        self.extended_limit = extended_limit
        self.unit_name = unit_name
        self.image_name_front = image_name_front
        self.image_name_back = image_name_back
        self.unit_id = unit_id
        self.is_flipped = is_flipped
        self.is_in_battle_hex = (True if math.isnan(self.move_range) else False)
        self.is_extended_range = is_extended_range
        self.attack_modifier = attack_modifier

        if nationality == 'Japan':
            self.player = enums.Player.JAPAN
        else:
            self.player = enums.Player.ALLIES

        self.damage_flipped = False
        self.damage_eliminated = False

    def combat_factor(self):

        combat_factor = self.attack_front

        if self.is_flipped | self.damage_flipped:
            combat_factor = self.attack_back

        combat_factor += self.attack_modifier

        if self.is_extended_range:
            combat_factor = int(math.ceil(combat_factor / 2))

        if self.damage_eliminated | (math.isnan(self.move_range) & (not self.is_in_battle_hex)):
            combat_factor = 0

        return int(math.ceil(combat_factor))

    def loss_delta(self):

        if self.is_flipped:
            loss_delta = self.attack_back
        else:
            loss_delta = self.attack_front - self.attack_back

        return loss_delta

    def damage_applied(self):
        damage_applied = 0

        if self.damage_flipped:
            damage_applied += self.defense

        if self.damage_eliminated:
            damage_applied += self.defense

        return damage_applied

