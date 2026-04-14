import math

class CostEngine:
    def __init__(
        self,
        structure_data: dict,
        construction_commander_level: int = 0,
        anti_gravity_level: int = 0
    ):
        self.data = structure_data
        self.cc = construction_commander_level
        self.ag = anti_gravity_level

    # -----------------------------------------
    # COST
    # -----------------------------------------
    def next_level_cost(self, structure: str, current_level: int) -> float:
        base_cost = self.data[structure]["base_cost"]

        # Cost scaling
        raw_cost = base_cost * (1.5 ** current_level)

        # Construction Commander discount
        discount = 0.01 * self.cc
        effective_cost = raw_cost * (1 - discount)

        return effective_cost

    # -----------------------------------------
    # BUILD TIME
    # -----------------------------------------
    def next_level_build_time(
        self,
        structure: str,
        current_level: int,
        construction_output: float
    ) -> float:
        cost = self.next_level_cost(structure, current_level)

        # Base build time
        time = cost / construction_output

        # Anti‑Gravity applies only to orbital structures
        if self.data[structure].get("orbital", False):
            ag_multiplier = max(1 - 0.05 * self.ag, 0.10)
            time *= ag_multiplier

        return time