import sys
from pathlib import Path

# ---------------------------------------------------------
# Ensure project root is on PYTHONPATH (Streamlit fix)
# ---------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

import streamlit as st
import pandas as pd

from model.progressive_planner import ProgressiveBasePlanner

# ---------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------
st.set_page_config(
    page_title="Astro Empires Base Optimiser",
    layout="wide",
)

st.title("🛰️ Astro Empires Base Optimiser")

st.markdown(
    """
    Progressive build‑order planner for **Astro Empires**.

    - Uses **marginal efficiency**
    - Builds **support only when required**
    - Handles **game mechanics** (e.g. Spaceport trade routes)
    """
)

# ---------------------------------------------------------
# SIDEBAR: GAME SETTINGS
# ---------------------------------------------------------
st.sidebar.header("⚙️ Game Settings")

astro_type = st.sidebar.selectbox(
    "Astro Type",
    ["Rocky", "Icy", "Gas"],
    index=0,
)

is_moon = st.sidebar.checkbox("Moon", value=True)

position = st.sidebar.number_input(
    "Position",
    min_value=1,
    max_value=25,
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
    value=10,
)

production_commander = st.sidebar.number_input(
    "Production Commander",
    min_value=0,
    max_value=25,
    value=16,
)

anti_gravity = st.sidebar.number_input(
    "Anti‑Gravity Level",
    min_value=0,
    max_value=25,
    value=5,
)

# ---------------------------------------------------------
# TARGET STRUCTURES
# ---------------------------------------------------------
st.subheader("🏗️ Target Structures")

default_targets = {
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
}

df_targets = pd.DataFrame(
    list(default_targets.items()),
    columns=["Structure", "Target Level"],
)

edited_df = st.data_editor(
    df_targets,
    num_rows="fixed",
    use_container_width=True,
)

STRUCTURE_TARGET = {
    row["Structure"]: int(row["Target Level"])
    for _, row in edited_df.iterrows()
    if int(row["Target Level"]) > 0
}

# ---------------------------------------------------------
# RUN OPTIMISER
# ---------------------------------------------------------
st.divider()

run = st.button("🚀 Run Optimiser", type="primary")

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

    st.success("Optimisation complete ✅")

    # -----------------------------------------------------
    # SUMMARY
    # -----------------------------------------------------
    st.subheader("📊 Summary")

    totals = result["totals"]

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Total Build Time",
        f"{totals['total_days']:.1f} days",
    )
    col2.metric(
        "Total Credits",
        f"{int(totals['total_credits']):,} cr",
    )
    col3.metric(
        "Build Steps",
        len(result["steps"]),
    )

    base_prod, prod_adj = totals["production"]
    base_con, con_adj = totals["construction"]

    st.markdown(
        f"""
        **Production**: {base_prod:.1f} → **{prod_adj:.1f}**  
        **Construction**: {base_con:.1f} → **{con_adj:.1f}**  
        **Research**: {totals['research']:.1f}  
        **Economy**: {totals['economy']}
        """
    )

    # -----------------------------------------------------
    # BUILD ORDER TABLE
    # -----------------------------------------------------
    st.divider()
    st.subheader("📋 Progressive Build Order")

    rows = []
    for i, step in enumerate(result["steps"], start=1):
        rows.append(
            {
                "Step": i,
                "Structure": step["structure"],
                "Gain": step["gain"],
                "Reason": step["reason"],
                "Build Time (days)": round(step["build_time_hours"] / 24, 2),
                "Cost (cr)": int(step["credit_cost"]),
                "Type": (
                    "Support"
                    if "constraint fix" in step["reason"].lower()
                    or "support" in step["reason"].lower()
                    else "Target"
                ),
            }
        )

    df_steps = pd.DataFrame(rows)

    st.dataframe(
        df_steps,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Cost (cr)": st.column_config.NumberColumn(format="%d"),
            "Build Time (days)": st.column_config.NumberColumn(format="%.2f"),
            "Type": st.column_config.CategoricalColumn(
                categories=["Target", "Support"],
                colors={
                    "Target": "blue",
                    "Support": "orange",
                },
            ),
        },
    )