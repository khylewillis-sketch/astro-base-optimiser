from model.base_state import BaseState

def run_test():
    print("=== BaseState Test — ===")

    # --------------------------------------------------------------
    # Base Inputs (Rocky / Moon / Position 3)
    # --------------------------------------------------------------
    astro_type = "Rocky"
    is_moon = True
    position = 2

    tech_levels = {
        "Energy": 38,          # +190%
        "AI": 20,              # +100%
        "Cybernetics": 22,     # +110%
        "AG": 0                # Not used for stats
    }

    # --------------------------------------------------------------
    # Structure levels — EXACT from your example
    # --------------------------------------------------------------
    structure_levels = {
        "Urban Structures": 27,
        "Solar Plants": 5,
        "Fusion Plants": 21,
        "Antimatter Plants": 12,
        "Orbital Plants": 4,

        "Research Labs": 20,
        "Metal Refineries": 33,
        "Robotic Factories": 28,
        "Shipyards": 28,
        "Orbital Shipyards": 14,

        "Spaceports": 30,
        "Nanite Factories": 23,
        "Android Factories": 21,
        "Economic Centers": 20,

        "Terraform": 21,
        "Multi-Level Platforms": 10,
        "Orbital Base": 11,
        "Jump Gate": 11,
        "Biosphere Modification": 1,

        "Planetary Shield": 2,   
        "Planetary Ring": 4,     

        "Command Centers": 8
    }

    # --------------------------------------------------------------
    # Build BaseState object
    # --------------------------------------------------------------
    base = BaseState(
        astro_type=astro_type,
        position=position,
        tech_levels=tech_levels,
        structure_levels=structure_levels,
        is_moon=is_moon
    )

    results = base.compute_all()

    # --------------------------------------------------------------
    # PRINT EVERYTHING
    # --------------------------------------------------------------
    print("\n--- Effective Astro Stats (Terrain + Orbital) ---")
    print(f"Metal:       {base.metal}")
    print(f"Gas:         {base.gas}")
    print(f"Crystals:    {base.crystals}")
    print(f"Fertility:   {base.fertility}")
    print(f"Solar:       {base.solar}")

    print("\n--- Population ---")
    pop = results["population"]
    print(f"Population Required: {pop['required']}")
    print(f"Population Capacity: {pop['capacity']}")
    print(f"Population Surplus:  {pop['surplus']}")

    print("\n--- Area ---")
    area = results["area"]
    print(f"Base Area:      {area['base_area']}")
    print(f"Area Added:     {area['area_added']}")
    print(f"Area Used:      {area['area_used']}")
    print(f"Area Remaining: {area['remaining']}")

    print("\n--- Energy ---")
    energy = results["energy"]
    print(f"Energy Produced:  {energy['produced']:.1f}")
    print(f"Energy Consumed:  {energy['consumed']:.1f}")
    print(f"Energy Surplus:   {energy['surplus']:.1f}")

    print("\n--- Production ---")
    print(f"Production Total: {results['production']:.1f}")

    print("\n--- Construction ---")
    print(f"Construction Total: {results['construction']:.1f}")

    print("\n--- Economy ---")
    print(f"Economy Total: {results['economy']}")

    print("\n--- Research ---")
    print(f"Research Total: {results['research']:.1f}")

    print("\n=== TEST COMPLETE ===")


if __name__ == "__main__":
    run_test()