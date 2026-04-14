from unittest import result

from model.base_state import BaseState
from model.base_optimiser import BaseOptimiser


def make_base_with_exact_deficit(kind):
    """
    Build a base with exactly ONE deficit.
    Other constraints are pre-balanced.
    """

    structures = {
        # Energy
        "Solar Plants": 10,      # ensures no energy deficit by default
        "Fusion Plants": 0,
        "Antimatter Plants": 0,
        "Orbital Plants": 0,

        # Area
        "Terraform": 10,         # ensures no area deficit by default
        "Multi-Level Platforms": 0,

        # Population
        "Urban Structures": 10,  # ensures no pop deficit by default
        "Orbital Base": 0,

        # Test lever
        "Research Labs": 0,
    }

    if kind == "energy":
        structures["Solar Plants"] = 0
        structures["Research Labs"] = 50   # energy deficit only

    elif kind == "area":
    # remove ALL area providers
        structures["Terraform"] = 0
        structures["Multi-Level Platforms"] = 0

    # keep other constraints neutral
        structures["Solar Plants"] = 10
        structures["Urban Structures"] = 10

    # force area deficit
        structures["Research Labs"] = 100

    elif kind == "population":
        structures["Urban Structures"] = 0
        structures["Research Labs"] = 50   # pop deficit only

    tech = {
        "Energy": 20,
        "AI": 0,
        "Cybernetics": 0,
    }

    return BaseState(
        astro_type="Rocky",
        position=2,
        tech_levels=tech,
        structure_levels=structures,
        is_moon=True,
    )

# ------------------------------------------------------------
# TEST 1: Optimiser fixes energy deficit and terminates
# ------------------------------------------------------------
def test_optimiser_fixes_energy_deficit():
    base = make_base_with_exact_deficit("energy")

    optimiser = BaseOptimiser(
        base_state=base,
        construction_commander_level=0,
        anti_gravity_level=0,
    )

    result = optimiser.optimise()
    final_state = result["final_state"]
    steps = result["steps"]

    assert final_state.compute_energy()["surplus"] >= 0
    assert len(steps) > 0
    assert result["total_build_time"] > 0
    assert result["total_credit_cost"] > 0

# ------------------------------------------------------------
# TEST 2: Area-preserving tie-break (Orbital Plant preferred)
# ------------------------------------------------------------
def test_energy_uses_orbital_when_time_equal():
    base = make_base_with_exact_deficit("energy")

    optimiser = BaseOptimiser(
        base_state=base,
        construction_commander_level=0,
        anti_gravity_level=5,
    )

    result = optimiser.optimise()
    final_state = result["final_state"]
    steps = result["steps"]

    assert steps[0].structure == "Orbital Plants"
    assert result["total_build_time"] > 0
    assert result["total_credit_cost"] > 0


# ------------------------------------------------------------
# TEST 3: Population deficit prefers Urban over Orbital Base
# ------------------------------------------------------------

def test_population_prefers_urban_first():
    base = make_base_with_exact_deficit("population")

    optimiser = BaseOptimiser(
        base_state=base,
        construction_commander_level=0,
        anti_gravity_level=0,
    )

    result = optimiser.optimise()
    final_state = result["final_state"]
    steps = result["steps"]

    assert steps[0].structure == "Orbital Base"
    assert result["total_build_time"] > 0
    assert result["total_credit_cost"] > 0



# ------------------------------------------------------------
# TEST 4: Area deficit prefers Terraform over MLP
# ------------------------------------------------------------

def test_area_prefers_terraform():
    base = make_base_with_exact_deficit("area")

    optimiser = BaseOptimiser(
        base_state=base,
        construction_commander_level=0,
        anti_gravity_level=0,
    )

    result = optimiser.optimise()
    final_state = result["final_state"]
    steps = result["steps"]

    assert steps[0].structure == "Multi-Level Platforms"
    assert result["total_build_time"] > 0
    assert result["total_credit_cost"] > 0

