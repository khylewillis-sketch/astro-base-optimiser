from model.cost_engine import CostEngine

def test_cost_scaling():
    data = {
        "Test": {"base_cost": 100, "orbital": False}
    }
    ce = CostEngine(data)

    assert ce.next_level_cost("Test", 0) == 100
    assert ce.next_level_cost("Test", 1) == 150
    assert ce.next_level_cost("Test", 2) == 225

def test_commander_discount():
    data = {
        "Test": {"base_cost": 100, "orbital": False}
    }
    ce = CostEngine(data, construction_commander_level=10)

    cost = ce.next_level_cost("Test", 0)
    assert round(cost, 2) == 90.0

def test_orbital_ag_reduction():
    data = {
        "Orbital": {"base_cost": 1000, "orbital": True}
    }
    ce = CostEngine(data, anti_gravity_level=6)

    t = ce.next_level_build_time(
        "Orbital",
        current_level=0,
        construction_output=100
    )

    # Base time = 10
    # AG reduction = 30% → multiplier 0.7
    assert round(t, 2) == 7.0