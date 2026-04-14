from copy import deepcopy
from model.base_state import BaseState
from model.cost_engine import CostEngine

class OptimiserStep:
    """
    Represents a single optimiser decision.
    build_time_hours is in HOURS.
    """

    def __init__(
        self,
        structure: str,
        reason: str,
        build_time: float,
        credit_cost: float,
        area_delta: int,
    ):
        self.structure = structure
        self.reason = reason
        self.build_time_hours = build_time
        self.credit_cost = credit_cost
        self.area_delta = area_delta


class BaseOptimiser:
    """
    Constraint-aware Astro Empires base optimiser.

    Philosophy:
      * Fix only what is broken
      * Priority: Area -> Energy -> Population
      * Compare by efficiency (not absolute value)
    """

    def __init__(
        self,
        base_state: BaseState,
        construction_commander_level: int = 0,
        anti_gravity_level: int = 0,
    ):
        self.initial = base_state
        self.structures = deepcopy(base_state.slv)
        self.steps: list[OptimiserStep] = []

        self.cost_engine = CostEngine(
            structure_data=base_state.struct_data,
            construction_commander_level=construction_commander_level,
            anti_gravity_level=anti_gravity_level,
        )

    # ---------------------------------------------------------
    # PUBLIC ENTRY POINT
    # ---------------------------------------------------------
    def optimise(self):
        """
        Optimise until the base is valid.

        Returns:
          {
            final_state,
            steps,
            total_build_time_hours,
            total_credit_cost
          }
        """
        while True:
            state = self._recompute()
            state.compute_construction()

            area = state.compute_area()["remaining"]
            energy = state.compute_energy()["surplus"]
            population = state.compute_population()["surplus"]

            if area < 0:
                candidates = self._area_candidates(state)
                constraint = "area"

            elif energy < 0:
                candidates = self._energy_candidates(state)
                constraint = "energy"

            elif population < 0:
                candidates = self._population_candidates(state)
                constraint = "population"

            else:
                total_time = sum(step.build_time_hours for step in self.steps)
                total_cost = sum(step.credit_cost for step in self.steps)

                return {
                    "final_state": state,
                    "steps": self.steps,
                    "total_build_time_hours": total_time,
                    "total_credit_cost": total_cost,
                }

            best = self._select_best_candidate(candidates, constraint)
            self.structures[best.structure] = self.structures.get(best.structure, 0) + 1
            self.steps.append(best)

    # ---------------------------------------------------------
    # AREA CANDIDATES
    # ---------------------------------------------------------
    def _area_candidates(self, state):
        candidates = []

        options = {
            "Terraform": 5,
            "Multi-Level Platforms": 10,
        }

        for structure, area_gain in options.items():
            current_level = self.structures.get(structure, 0)

            cost = self.cost_engine.next_level_cost(structure, current_level)
            time_hours = self.cost_engine.next_level_build_time(
                structure, current_level, state.construction_total
            )

            candidates.append(
                OptimiserStep(
                    structure=structure,
                    reason=f"+{area_gain} area",
                    build_time=time_hours,
                    credit_cost=cost,
                    area_delta=area_gain,
                )
            )

        return candidates

    # ---------------------------------------------------------
    # ENERGY CANDIDATES
    # ---------------------------------------------------------
    def _energy_candidates(self, state):
        candidates = []

        mult = 1 + 0.05 * state.tech.get("Energy", 0) + 0.005

        options = {
            "Solar Plants": (state.solar * mult, -1),
            "Fusion Plants": (4 * mult, -1),
            "Antimatter Plants": (10 * mult, -1),
            "Orbital Plants": (12 * mult, 0),
        }

        for structure, (energy_gain, area_delta) in options.items():
            if energy_gain <= 0:
                continue

            current_level = self.structures.get(structure, 0)

            cost = self.cost_engine.next_level_cost(structure, current_level)
            time_hours = self.cost_engine.next_level_build_time(
                structure, current_level, state.construction_total
            )

            candidates.append(
                OptimiserStep(
                    structure=structure,
                    reason=f"+{energy_gain:.1f} energy",
                    build_time=time_hours,
                    credit_cost=cost,
                    area_delta=area_delta,
                )
            )

        return candidates

    # ---------------------------------------------------------
    # POPULATION CANDIDATES (Bio‑Mod handled correctly)
    # ---------------------------------------------------------
    def _population_candidates(self, state):
        candidates = []

        population_surplus = state.compute_population()["surplus"]
        area_remaining = state.compute_area()["remaining"]

        urban_count = self.structures.get("Urban Structures", 0)
        orbital_base_count = self.structures.get("Orbital Base", 0)
        fertility = state.fertility

        # ---- Urban Structures ----
        if fertility > 0:
            structure = "Urban Structures"
            pop_gain = fertility
            current_level = urban_count

            cost = self.cost_engine.next_level_cost(structure, current_level)
            time_hours = self.cost_engine.next_level_build_time(
                structure, current_level, state.construction_total
            )

            candidates.append(
                OptimiserStep(
                    structure=structure,
                    reason=f"+{pop_gain} population",
                    build_time=time_hours,
                    credit_cost=cost,
                    area_delta=-1,
                )
            )

        # ---- Orbital Base ----
        structure = "Orbital Base"
        current_level = orbital_base_count

        cost = self.cost_engine.next_level_cost(structure, current_level)
        time_hours = self.cost_engine.next_level_build_time(
            structure, current_level, state.construction_total
        )

        candidates.append(
            OptimiserStep(
                structure=structure,
                reason="+10 population",
                build_time=time_hours,
                credit_cost=cost,
                area_delta=0,
            )
        )

        # ---- Biosphere Modification ----
        if (
            population_surplus < 0
            and urban_count >= 6
            and area_remaining <= 6
        ):
            structure = "Biosphere Modification"
            pop_gain = urban_count  # immediate effect on existing Urbans
            current_level = self.structures.get(structure, 0)

            cost = self.cost_engine.next_level_cost(structure, current_level)
            time_hours = self.cost_engine.next_level_build_time(
                structure, current_level, state.construction_total
            )

            candidates.append(
                OptimiserStep(
                    structure=structure,
                    reason=f"+{pop_gain} population (Bio‑Mod)",
                    build_time=time_hours,
                    credit_cost=cost,
                    area_delta=-1,
                )
            )

        return candidates

    # ---------------------------------------------------------
    # SELECTION LOGIC (CONSTRAINT-AWARE)
    # ---------------------------------------------------------
    def _select_best_candidate(self, candidates, constraint):
        """
        Area      -> area / hour
        Energy    -> energy / hour (area-penalised)
        Population-> population / hour (area-penalised)
        """

        def score(c):
            # Extract numeric delta from reason ("+10 population", "+34.9 energy")
            primary_delta = float(c.reason.split()[0][1:])

            efficiency = primary_delta / c.build_time_hours

            # Penalise area usage unless solving area itself
            if constraint != "area" and c.area_delta < 0:
                efficiency *= 0.5

            return efficiency

        return max(candidates, key=score)

    # ---------------------------------------------------------
    # INTERNAL
    # ---------------------------------------------------------
    def _recompute(self):
        return BaseState(
            astro_type=self.initial.astro_type,
            position=self.initial.position,
            tech_levels=self.initial.tech,
            structure_levels=self.structures,
            is_moon=self.initial.is_moon,
        )