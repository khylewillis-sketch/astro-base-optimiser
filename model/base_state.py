import os
from model.data_loader import load_all_data

class BaseState:
    """
    Fully accurate Astro Empires v1.5 base calculator.

    All structural, economic, production, construction, and population
    values are taken exclusively from the official AE 1.5 game tables:
    https://alpha.astroempires.com/tables.aspx?view=all  # [1](https://ares.astroempires.com/tables.aspx?view=structures)

    Implements:
      - Terrain stats + orbital bonuses
      - Population required & capacity
      - Area usage
      - Energy production & consumption (+EnergyTech)
      - Production using official AE 1.5 values (+Cyber)
      - Construction using MR/RF/NF/AF/Base20 only (+Cyber)
      - Economy from official values
      - Research = RL*6*(1 + 0.05*AI)
    """

    def __init__(self, astro_type, position, tech_levels, structure_levels,
                 is_moon=False, data_dir=None):

        data = load_all_data(data_dir)
        self.astro_data = data["astro_types"]
        self.struct_data = data["structures"]

        self.astro_type = astro_type
        self.position = position
        self.tech = tech_levels
        self.slv = structure_levels
        self.is_moon = is_moon

        # Terrain-derived values
        self.metal = 0
        self.gas = 0
        self.crystals = 0
        self.fertility = 0
        self.solar = 0

        self._compute_astro_modifiers()

        # Outputs
        self.population_required = 0
        self.population_capacity = 0
        self.area_total = 0
        self.energy_produced = 0
        self.energy_consumed = 0
        self.energy_surplus = 0
        self.production_total = 0
        self.construction_total = 0
        self.economy_total = 0
        self.research_total = 0

    # ---------------------------------------------------------
    # TERRAIN & ORBITAL MODIFIERS
    # ---------------------------------------------------------
    def _compute_astro_modifiers(self):
        """Apply official terrain stats + orbital bonuses (AE 1.5)."""
        a = self.astro_data[self.astro_type]

        self.metal = a["metal"]
        self.gas = a["gas"]
        self.crystals = a["crystals"]

        # Fertility = base + BM + orbital bonus (pos 2–3 → +1)
        base_fert = a["fertility"]
        bios = self.slv.get("Biosphere Modification", 0)
        fert_bonus = 1 if self.position in (2, 3) else 0
        self.fertility = base_fert + fert_bonus + bios

        # Solar = orbital (pos 1 = 4, ..., pos 5 = 0)
        self.solar = {1: 4, 2: 3, 3: 2, 4: 1, 5: 0}[self.position]

        # Gas orbital bonus (pos 4–5 → +1)
        if self.position in (4, 5):
            self.gas += 1

    # ---------------------------------------------------------
    # POPULATION
    # ---------------------------------------------------------
    def compute_population(self):
        required = 0

        for name, lvl in self.slv.items():
            pop_cost = self.struct_data[name].get("population", 0)
            required += pop_cost * lvl

        urb = self.slv.get("Urban Structures", 0)
        ob = self.slv.get("Orbital Base", 0)

        capacity = urb * self.fertility + ob * 10

        self.population_required = required
        self.population_capacity = capacity

        return {
            "required": required,
            "capacity": capacity,
            "surplus": capacity - required
        }
# ---------------------------------------------------------
    # AREA (with full diagnostics)
    # ---------------------------------------------------------
    def compute_area(self):
        """
        Returns:
          - base_area (planet/moon)
          - area_added (TF + MLP positive area)
          - area_used (sum of all negative-area structures)
          - remaining (base + added + used)
        """

        astro = self.astro_data[self.astro_type]
        base_area = astro["area_moon"] if self.is_moon else astro["area_planet"]

        area_added = 0
        area_used = 0

        for name, lvl in self.slv.items():
            area = self.struct_data[name].get("area", 0)

            if area > 0:
                area_added += area * lvl
            else:
                area_used += area * lvl

        remaining = base_area + area_added + area_used

        self.area_total = remaining

        return {
            "base_area": base_area,
            "area_added": area_added,
            "area_used": area_used,   # will be negative
            "remaining": remaining
        }
# ---------------------------------------------------------
    # ENERGY
    # ---------------------------------------------------------
    def compute_energy(self):
        """
        Final AE 1.5 (server-accurate) energy rules:
          1. Sum raw energy from all plants
          2. Apply Energy Tech multiplier ONCE (ceil)
          3. Add base bonus (1 + solar)
        """
        import math

        eTech = self.tech.get("Energy", 0)
        mult = 1 + 0.05 * eTech + 0.005

        raw_subtotal = 0
        consumed = 0

        for name, lvl in self.slv.items():
            s = self.struct_data[name]
            e = s.get("energy", 0)

            # Energy consumption
            if isinstance(e, int) and e < 0:
                consumed += (-e) * lvl
                continue

            # Energy production
            if e == "solar":
                base = self.solar
            elif e == "gas":
                base = self.gas
            else:
                base = e

            raw_subtotal += base * lvl

        # Apply tech AFTER full raw subtotal
        tech_scaled = math.ceil(raw_subtotal * mult)

        # Hidden AE mechanic: base = 1 + solar
        base_bonus = 1 + self.solar

        produced = tech_scaled + base_bonus

        self.energy_produced = produced
        self.energy_consumed = consumed
        self.energy_surplus = produced - consumed

        return {
            "produced": produced,
            "consumed": consumed,
            "surplus": produced - consumed
        }
    # ---------------------------------------------------------
    # PRODUCTION
    # ---------------------------------------------------------
    def compute_production(self):
        """
        Production contributions from official AE 1.5 tables:
        MR = metal per level
        CM = crystals per level
        RF = 2
        NF = 4
        AF = 6
        SY = 2
        OSY = 8
        Cyber = +5% per level
        """
        cyb = self.tech.get("Cybernetics", 0)
        mult = 1 + 0.05 * cyb

        prod = 0

        for name, lvl in self.slv.items():
            base = self.struct_data[name].get("production", 0)

            if base == "metal":
                base = self.metal
            elif base == "crystals":
                base = self.crystals

            if isinstance(base, int):
                prod += base * lvl

        prod *= mult
        self.production_total = prod
        return prod

    # ---------------------------------------------------------
    # CONSTRUCTION
    # ---------------------------------------------------------
    def compute_construction(self):
        """
        Construction (your server + official AE rules):
        Only MR, RF, NF, AF contribute + Base20.
        No SY/OSY construction.
        """
        cyb = self.tech.get("Cybernetics", 0)
        mult = 1 + 0.05 * cyb

        total = 20  # base construction

        MR = self.slv.get("Metal Refineries", 0)
        RF = self.slv.get("Robotic Factories", 0)
        NF = self.slv.get("Nanite Factories", 0)
        AF = self.slv.get("Android Factories", 0)

        total += MR * self.metal
        total += RF * 2
        total += NF * 4
        total += AF * 6

        total *= mult
        self.construction_total = total
        return total

    # ---------------------------------------------------------
    # ECONOMY
    # ---------------------------------------------------------
    def compute_economy(self):
        econ = 0

        for name, lvl in self.slv.items():
            e = self.struct_data[name].get("economy", 0)

            if e == "crystals":
                econ += self.crystals * lvl
            else:
                econ += e * lvl

        self.economy_total = econ
        return econ

    # ---------------------------------------------------------
    # RESEARCH
    # ---------------------------------------------------------
    def compute_research(self):
        labs = self.slv.get("Research Labs", 0)
        base = labs * 6

        ai = self.tech.get("AI", 0)
        mult = 1 + 0.05 * ai

        total = base * mult
        self.research_total = total
        return total

    # ---------------------------------------------------------
    # MASTER WRAPPER
    # ---------------------------------------------------------
    def compute_all(self):
        return {
            "population": self.compute_population(),
            "area": self.compute_area(),
            "energy": self.compute_energy(),
            "production": self.compute_production(),
            "construction": self.compute_construction(),
            "economy": self.compute_economy(),
            "research": self.compute_research()
        }