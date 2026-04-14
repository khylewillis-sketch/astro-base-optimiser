from model.progressive_planner import ProgressiveBasePlanner

# ---------------------------------------------------------
# PLAYER INPUT
# ---------------------------------------------------------

TECH_LEVELS = {
    "Energy": 38,
    "AI": 20,
    "Cybernetics": 22,
}

STRUCTURE_TARGET = {
    "Metal Refineries": 33,
    "Robotic Factories": 28,
    "Nanite Factories": 23,
    "Android Factories": 21,

    "Shipyards": 28,
    "Orbital Shipyards": 14,

    "Research Labs": 20,
    "Spaceports": 30,
    "Economic Centers": 20,
    "Command Centers": 8,

    "Planetary Shield": 2,
    "Planetary Ring": 4,

    # Start with ZERO support buildings
    "Solar Plants": 0,
    "Fusion Plants": 0,
    "Antimatter Plants": 0,
    "Orbital Plants": 0,
    "Urban Structures": 0,
    "Orbital Base": 0,
    "Terraform": 0,
    "Multi-Level Platforms": 0,
}

ASTRO_TYPE = "Rocky"
POSITION = 2
IS_MOON = True

CONSTRUCTION_COMMANDER_LEVEL = 0
PRODUCTION_COMMANDER_LEVEL = 17
ANTI_GRAVITY_LEVEL = 5

# ---------------------------------------------------------
# RUN PROGRESSIVE PLANNER
# ---------------------------------------------------------

planner = ProgressiveBasePlanner(
    target_structures=STRUCTURE_TARGET,
    astro_type=ASTRO_TYPE,
    position=POSITION,
    tech_levels=TECH_LEVELS,
    is_moon=IS_MOON,
    construction_commander_level=CONSTRUCTION_COMMANDER_LEVEL,
    production_commander_level=PRODUCTION_COMMANDER_LEVEL,
    anti_gravity_level=ANTI_GRAVITY_LEVEL,
)

result = planner.plan()
steps = result["steps"]
totals = result["totals"]

# ---------------------------------------------------------
# FORMATTERS
# ---------------------------------------------------------

def format_time(hours: float) -> str:
    days = hours / 24
    if days >= 1:
        return f"{days:.2f} days"
    elif hours >= 1:
        return f"{hours:.2f} hours"
    else:
        return f"{hours * 60:.1f} minutes"

# ---------------------------------------------------------
# PRINT PROGRESSIVE BUILD ORDER
# ---------------------------------------------------------

print("\n=== PROGRESSIVE BUILD ORDER ===\n")

for i, step in enumerate(steps, start=1):
    print(
        f"{i:03d}. {step['structure']:<22} | "
        f"{step['gain']:<18} | "
        f"{step['reason']:<45} | "
        f"Time: {format_time(step['build_time_hours']):>10} | "
        f"Cost: {step['credit_cost']:>9,.0f} cr"
    )

# ---------------------------------------------------------
# TOTALS
# ---------------------------------------------------------

print("\n=== TOTALS ===\n")

print(f"Total build time : {totals['total_days']:.2f} days")
print(f"Total credit cost: {totals['total_credits']:,.0f} cr")

base_prod, prod_with_cmd = totals["production"]
base_con, con_with_cmd = totals["construction"]

print(f"\nProduction   : {base_prod:.1f} [{prod_with_cmd:.1f}]")
print(f"Construction: {base_con:.1f} [{con_with_cmd:.1f}]")
print(f"Research     : {totals['research']:.1f}")
print(f"Economy      : {totals['economy']}")
