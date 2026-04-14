from copy import deepcopy
from model.base_state import BaseState
from model.base_optimiser import BaseOptimiser
from model.cost_engine import CostEngine


class ProgressiveBasePlanner:
    """
    Progressive build-cycle planner with marginal efficiency optimisation.

    Special handling:
    - Spaceports evaluated as bundles to next trade-route threshold
    """

    SPACEPORT_STEP = 5  # trade route every 5 spaceports

    def __init__(
        self,
        target_structures: dict,
        astro_type: str,
        position: int,
        tech_levels: dict,
        is_moon: bool,
        construction_commander_level: int = 0,
        production_commander_level: int = 0,
        anti_gravity_level: int = 0,
    ):
        self.target = target_structures
        self.astro_type = astro_type
        self.position = position
        self.tech_levels = tech_levels
        self.is_moon = is_moon

        self.cc_level = construction_commander_level
        self.pc_level = production_commander_level
        self.ag_level = anti_gravity_level

        self.current_structures = {k: 0 for k in target_structures}
        self.steps = []

        # When a Spaceport bundle is active, we force SP builds
        self.active_spaceport_target = None

    # ---------------------------------------------------------
    # PUBLIC ENTRY POINT
    # ---------------------------------------------------------
    def plan(self):
        while not self._target_complete():
            base_state = self._current_state()

            # Forced Spaceport bundle mode
            if self.active_spaceport_target is not None:
                structure = "Spaceports"
                reason = (
                    f"Completing Spaceport bundle "
                    f"({self.current_structures['Spaceports']} → "
                    f"{self.active_spaceport_target})"
                )
            else:
                best, second = self._next_best_target_candidates(base_state)
                if best is None:
                    structure = self._any_remaining_target()
                    reason = "Completion phase"
                else:
                    _, structure, _ = best
                    reason = self._choice_reason(best, second)

                    # If Spaceports win, lock bundle
                    if structure == "Spaceports":
                        self._activate_spaceport_bundle()

            # Tentative build
            self.current_structures[structure] = self.current_structures.get(structure, 0) + 1
            support_step = self._first_support_step_needed()

            if support_step:
                self.current_structures[structure] -= 1
                structure = support_step.structure
                reason = "Support required (constraint fix)"

            base_state = self._current_state()
            self.steps.append(self._build_step_record(structure, base_state, reason))
            self.current_structures[structure] = self.current_structures.get(structure, 0) + 1

            # Check if Spaceport bundle completed
            if (
                self.active_spaceport_target is not None
                and self.current_structures["Spaceports"]
                >= self.active_spaceport_target
            ):
                self.active_spaceport_target = None

        # Final support cleanup
        while True:
            support_step = self._first_support_step_needed()
            if not support_step:
                break
            structure = support_step.structure
            base_state = self._current_state()
            self.steps.append(
                self._build_step_record(structure, base_state, "Final support cleanup")
            )
            self.current_structures[structure] = self.current_structures.get(structure, 0) + 1

        return self._final_result()

    # ---------------------------------------------------------
    # SPACEPORT BUNDLE LOGIC
    # ---------------------------------------------------------
    def _activate_spaceport_bundle(self):
        current = self.current_structures["Spaceports"]
        next_threshold = ((current // self.SPACEPORT_STEP) + 1) * self.SPACEPORT_STEP
        self.active_spaceport_target = min(
            next_threshold, self.target["Spaceports"]
        )

    def _spaceport_bundle_efficiency(self, base_state):
        current = self.current_structures.get("Spaceports", 0)

        # Next trade route threshold: 5, 10, 15, ...
        target = ((current // self.SPACEPORT_STEP) + 1) * self.SPACEPORT_STEP
        target = min(target, self.target.get("Spaceports", target))

        needed = target - current
        if needed <= 0:
            return float("inf")

        cost_engine = CostEngine(
            structure_data=base_state.struct_data,
            construction_commander_level=self.cc_level,
            anti_gravity_level=self.ag_level,
        )

        # --- total cost to reach next threshold ---
        total_cost = 0.0
        for i in range(needed):
            total_cost += cost_engine.next_level_cost(
                "Spaceports", current + i
            )

    # --- economy BEFORE ---
        econ_before = base_state.compute_economy()

    # --- simulate reaching threshold ---
        next_structures = deepcopy(self.current_structures)
        next_structures["Spaceports"] = target

        next_state = BaseState(
            astro_type=self.astro_type,
            position=self.position,
            tech_levels=self.tech_levels,
            structure_levels=next_structures,
            is_moon=self.is_moon,
        )

    # --- economy AFTER ---
        econ_after = next_state.compute_economy()

        delta = econ_after - econ_before
        if delta <= 0:
            return float("inf")
    
        return total_cost / delta

    # ---------------------------------------------------------
    # STATE / SUPPORT
    # ---------------------------------------------------------
    def _current_state(self):
        return BaseState(
            astro_type=self.astro_type,
            position=self.position,
            tech_levels=self.tech_levels,
            structure_levels=deepcopy(self.current_structures),
            is_moon=self.is_moon,
        )

    def _first_support_step_needed(self):
        optimiser = BaseOptimiser(
            base_state=self._current_state(),
            construction_commander_level=self.cc_level,
            anti_gravity_level=self.ag_level,
        )
        steps = optimiser.optimise()["steps"]
        return steps[0] if steps else None

    def _target_complete(self):
        return all(
            self.current_structures.get(s, 0) >= lvl
            for s, lvl in self.target.items()
        )

    def _any_remaining_target(self):
        for s, lvl in self.target.items():
            if self.current_structures.get(s, 0) < lvl:
                return s
        raise RuntimeError("Invariant error")

    # ---------------------------------------------------------
    # STRATEGIC GATES
    # ---------------------------------------------------------
    def _prod_con_complete(self):
        for s, lvl in self.target.items():
            if self.current_structures.get(s, 0) >= lvl:
                continue
            if self._structure_output_type(s) in ("production", "construction"):
                return False
        return True

    # ---------------------------------------------------------
    # TARGET SELECTION
    # ---------------------------------------------------------
    def _next_best_target_candidates(self, base_state):
        scored = []
        prod_con_done = self._prod_con_complete()

        for structure, target_level in self.target.items():
            current_level = self.current_structures.get(structure, 0)
            if current_level >= target_level:
                continue

            output_type = self._structure_output_type(structure)
            if output_type is None:
                continue

            if output_type in ("research", "economy") and not prod_con_done:
                continue

            if structure == "Spaceports":
                eff = self._spaceport_bundle_efficiency(base_state)
            else:
                eff = self._marginal_efficiency(
                    structure, current_level, base_state, output_type
                )

            scored.append((eff, structure, output_type))

        if not scored:
            return None, None

        scored.sort(key=lambda x: x[0])
        return scored[0], scored[1] if len(scored) > 1 else None

    # ---------------------------------------------------------
    # EXPLANATION / MATH
    # ---------------------------------------------------------
    def _choice_reason(self, best, second):
        v1, s1, _ = best
        if not second:
            return f"{s1} chosen (only viable option)"
        v2, s2, _ = second
        return f"{s1} chosen: {v1:,.1f} < {s2} {v2:,.1f}"

    def _marginal_efficiency(self, structure, current_level, base_state, output_type):
        cost_engine = CostEngine(
            structure_data=base_state.struct_data,
            construction_commander_level=self.cc_level,
            anti_gravity_level=self.ag_level,
        )

        cost = cost_engine.next_level_cost(structure, current_level)
        before = self._compute_output(base_state, output_type)

        next_structures = deepcopy(self.current_structures)
        next_structures[structure] = current_level + 1

        next_state = BaseState(
            astro_type=self.astro_type,
            position=self.position,
            tech_levels=self.tech_levels,
            structure_levels=next_structures,
            is_moon=self.is_moon,
        )

        after = self._compute_output(next_state, output_type)
        delta = after - before

        return float("inf") if delta <= 0 else cost / delta

    def _compute_output(self, state, output_type):
        if output_type == "production":
            return state.compute_production()
        if output_type == "construction":
            return state.compute_construction()
        if output_type == "research":
            return state.compute_research()
        if output_type == "economy":
            return state.compute_economy()
        raise ValueError(output_type)

    # ---------------------------------------------------------
    # STEP RECORDING
    # ---------------------------------------------------------
    def _build_step_record(self, structure, base_state, reason):
        cost_engine = CostEngine(
            structure_data=base_state.struct_data,
            construction_commander_level=self.cc_level,
            anti_gravity_level=self.ag_level,
        )

        lvl = self.current_structures.get(structure, 0)
        cost = cost_engine.next_level_cost(structure, lvl)
        time = cost_engine.next_level_build_time(
            structure, lvl, base_state.compute_construction()
        )

        return {
            "structure": structure,
            "reason": reason,
            "gain": self._gain_description(structure, base_state),
            "build_time_hours": time,
            "credit_cost": cost,
        }

    def _gain_description(self, structure, base_state):
        ot = self._structure_output_type(structure)
        if ot == "production":
            return "+production"
        if ot == "construction":
            return "+construction"
        if structure == "Terraform":
            return "+5 area"
        if structure == "Multi-Level Platforms":
            return "+10 area"
        if "Plants" in structure:
            return "+energy"
        if structure == "Urban Structures":
            return f"+{base_state.fertility} population"
        return ""

    # ---------------------------------------------------------
    # STRUCTURE CLASSIFICATION
    # ---------------------------------------------------------
    def _structure_output_type(self, structure):
        if structure in (
            "Metal Refineries",
            "Robotic Factories",
            "Nanite Factories",
            "Android Factories",
            "Shipyards",
            "Orbital Shipyards",
        ):
            return "production"

        if structure in ("Command Centers",):
            return "construction"

        if structure in ("Research Labs",):
            return "research"

        if structure in ("Economic Centers", "Spaceports"):
            return "economy"

        return None

    # ---------------------------------------------------------
    # FINAL TOTALS
    # ---------------------------------------------------------
    def _final_result(self):
        state = self._current_state()

        total_hours = sum(s["build_time_hours"] for s in self.steps)
        total_cost = sum(s["credit_cost"] for s in self.steps)

        base_prod = state.compute_production()
        base_con = state.compute_construction()

        prod_adj = base_prod * (1 + 0.01 * self.pc_level)
        con_adj = base_con * (1 + 0.01 * self.cc_level)

        return {
            "steps": self.steps,
            "totals": {
                "total_days": total_hours / 24,
                "total_credits": total_cost,
                "production": (base_prod, prod_adj),
                "construction": (base_con, con_adj),
                "research": state.compute_research(),
                "economy": state.compute_economy(),
            },
        }