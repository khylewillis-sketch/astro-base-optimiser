# =========================================================
# Imports & Paths
# =========================================================
import sys
import json
from pathlib import Path
from collections import defaultdict

import streamlit as st
import pandas as pd

from model.progressive_planner import ProgressiveBasePlanner

# =========================================================
# Paths & PYTHONPATH
# =========================================================
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

# =========================================================
# Load Data (Single Source of Truth)
# =========================================================
with open(DATA_DIR / "astro_types.json", "r") as f:
    ASTRO_TYPES = json.load(f)

with open(DATA_DIR / "structures.json", "r") as f:
    STRUCTURES = json.load(f)

# =========================================================
# Page Config
# =========================================================
st.set_page_config(
    page_title="Astro Empires Base Optimiser",
    layout="wide",
)

st.title("Astro Empires Base Optimiser")

# =========================================================
# SIDEBAR — BASE SETTINGS
# =========================================================
st.sidebar.header("Astro Base Type")

astro_type_names = sorted(ASTRO_TYPES.keys())
astro_type = st.sidebar.selectbox(
    "Astro Type",
    astro_type_names,
    index=astro_type_names.index("Rocky") if "Rocky" in astro_type_names else 0,
)

is_moon = st.sidebar.checkbox("Moon", value=True)

position = st.sidebar.number_input(
    "Position",
    min_value=1,
    max_value=6,
    value=2,
)

st.sidebar.divider()
st.sidebar.subheader("Tech Levels")

tech_energy = st.sidebar.number_input("Energy Tech", 0, 60, 38)
tech_ai = st.sidebar.number_input("AI Tech", 0, 60, 20)
tech_cyber = st.sidebar.number_input("Cybernetics Tech", 0, 60, 22)

TECH_LEVELS = {
    "Energy": tech_energy,
    "AI": tech_ai,
    "Cybernetics": tech_cyber,
}

st.sidebar.divider()
st.sidebar.subheader("Commanders")

construction_commander = st.sidebar.number_input(
    "Construction Commander",
    min_value=0,
    max_value=25,
    value=0,
)

production_commander = st.sidebar.number_input(
    "Production Commander",
    min_value=0,
    max_value=25,
    value=16,
)

anti_gravity = st.sidebar.number_input(
    "Anti-Gravity Level",
    min_value=0,
    max_value=25,
    value=5,
)

DEFAULT_TARGET_LEVELS = {
    # Production / Construction
    "Metal Refineries": 25,
    "Robotic Factories": 20,
    "Nanite Factories": 15,
    "Android Factories": 10,
    "Shipyards": 20,
    "Orbital Shipyards": 5,

    # Economy
    "Spaceports": 25,
    "Economic Centers": 15,
    "Capital": 10,

    # Special
    "Research Labs": 20,
    "Jump Gate": 10,

    # Defense
    "Planetary Shield": 2,
    "Planetary Ring": 4,
}


# =========================================================
# TARGET STRUCTURES (2‑COLUMN, ORDERED)
# =========================================================
st.subheader("Target Structures")

CATEGORY_LABELS = {
    "production": "Production / Construction",
    "economy": "Economy",
    "research": "Research",
    "defense": "Defense",
}

STRUCTURE_GROUPS = defaultdict(list)
for name, data in STRUCTURES.items():
    STRUCTURE_GROUPS[data.get("category")].append(name)

STRUCTURE_TARGET = {}

left_col, right_col = st.columns(2)

def render_section(container, section_key, categories):
    names = []
    for cat in categories:
        names.extend(STRUCTURE_GROUPS.get(cat, []))
    if not names:
        return

    names = sorted(names, key=lambda s: STRUCTURES[s].get("order", 999))

    with container:
        st.markdown(f"### {CATEGORY_LABELS[section_key]}")
        df = pd.DataFrame({
            "Structure": names,
            "Target Level": [
                DEFAULT_TARGET_LEVELS.get(s, 0) for s in names
            ],
        })
        edited = st.data_editor(
            df,
            hide_index=True,
            num_rows="fixed",
            use_container_width=True,
            column_config={
                "Structure": st.column_config.TextColumn(disabled=True),
                "Target Level": st.column_config.NumberColumn(min_value=0, step=1),
            },
            key=f"targets_{section_key}",
        )
        for _, row in edited.iterrows():
            if row["Target Level"] > 0:
                STRUCTURE_TARGET[row["Structure"]] = int(row["Target Level"])

render_section(left_col, "production", ["production"])
render_section(left_col, "economy", ["economy"])
render_section(right_col, "research", ["research", "special"])
render_section(right_col, "defense", ["defense"])

# =========================================================
# RUN OPTIMISER
# =========================================================
st.divider()

run = st.button("Run Optimiser", type="primary")

if run:
    with st.spinner("Optimising build order..."):
        planner = ProgressiveBasePlanner(
            target_structures=STRUCTURE_TARGET,
            astro_type=astro_type,
            position=position,
            tech_levels=TECH_LEVELS,
            is_moon=is_moon,
            construction_commander_level=construction_commander,
            production_commander_level=production_commander,
            anti_gravity_level=anti_gravity,
        )
        result = planner.plan()

    st.success("Optimisation complete")

# =====================================================
# SUMMARY (AUTHORITATIVE ENGINE OUTPUTS)
# =====================================================
    st.subheader("Summary")

    totals = result["totals"]
    constraints = result["constraints"]

    # --- Headline metrics ---
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Build Time", f"{totals['total_days']:.1f} days")
    col2.metric("Total Credits", f"{int(totals['total_credits']):,} cr")
    col3.metric("Build Steps", len(result["steps"]))

    # --- Production / Construction / Research / Economy ---
    base_prod, adj_prod = totals["production"]
    base_con, adj_con = totals["construction"]

    st.markdown(
        f"""
        **Production**: {base_prod:.1f} → **{adj_prod:.1f}**  
        **Construction**: {base_con:.1f} → **{adj_con:.1f}**  
        **Research**: {totals['research']:.1f}  
        **Economy**: {totals['economy']:.1f}
        """
    )

    # --- Constraints (from optimiser, no UI math) ---
    pop = constraints["population"]
    energy = constraints["energy"]
    area = constraints["area"]

    st.markdown(
        f"""
        **Population surplus**: {pop['surplus']}  
        **Energy surplus**: {energy['surplus']}  
        **Area remaining**: {area['remaining']}
        """
    )


    # =====================================================
    # BASE OUTPUT — SUPPORT FEEDBACK (EXPLANATION ONLY)
    # =====================================================
    st.subheader("Base Output (Support Structures)")

    built_counts = defaultdict(int)
    for step in result["steps"]:
        built_counts[step["structure"]] += 1

    def support_table(axis, title):
        rows = []
        for structure, cfg in STRUCTURES.items():
            if cfg.get("support_axis") != axis:
                continue
            count = built_counts.get(structure, 0)
            if count == 0:
                continue
            rows.append(
                {
                    "Structure": structure,
                    "Count": count,
                    "_order": cfg.get("order", 999),
                }
            )
        if not rows:
            return
        df = (
            pd.DataFrame(rows)
            .sort_values("_order")
            .drop(columns="_order")
            .reset_index(drop=True)
        )
        st.markdown(f"### {title}")
        st.table(df)

    support_table("population", "Population")
    support_table("energy", "Energy")
    support_table("area", "Area")

    # =====================================================
    # PROGRESSIVE BUILD ORDER
    # =====================================================
    st.divider()
    st.subheader("Progressive Build Order")

    rows = []
    structure_levels = defaultdict(int)

    for i, step in enumerate(result["steps"], start=1):
        s = step["structure"]
        structure_levels[s] += 1
        rows.append(
            {
                "Step": i,
                "Structure": f"{s} [{structure_levels[s]}]",
                "Reason": step["reason"],
                "Cost (cr)": int(step["credit_cost"]),
                "Type": (
                    "Support"
                    if "support" in step["reason"].lower()
                    else "Target"
                ),
            }
        )

    st.dataframe(pd.DataFrame(rows), hide_index=True)