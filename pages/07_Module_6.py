import streamlit as st
import importlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# 1. DYNAMIC IMPORT
module_logic = importlib.import_module("utils.07_Module_6")
OERKineticModel = module_logic.OERKineticModel

st.set_page_config(page_title="Module 6: Kinetics", layout="wide")

# --- NAVIGATION HEADER ---
st.title("07 | Module 6: OER Kinetics")
col_nav, _ = st.columns([1, 5])
with col_nav:
    if st.button("⬅️ Back to Module 5"):
        st.switch_page("pages/06_Module_5.py")
st.divider()

# --- MAIN CONTENT ---
st.subheader("Reaction Rate & Surface Coverage")
st.info("Simulate how the catalyst surface evolves as you increase the voltage.")

# SITE IDENTITY
site_name = st.text_input("Active Site Name", value="Ni-Fe Site")

# STEP 1: ENERGETICS
st.write("#### 1. Input Energetics ($\Delta G$ in eV)")
with st.container(border=True):
    # Try to auto-fill if user has data from Module 4
    d1, d2, d3 = st.columns(3)
    dg1 = d1.number_input("H2O ads.", value=-0.32, format="%.3f")
    dg2 = d2.number_input("OH form.", value=1.32, format="%.3f")
    dg3 = d3.number_input("O form.", value=1.47, format="%.3f")
    dg4 = d1.number_input("OOH form.", value=1.51, format="%.3f")
    dg5 = d2.number_input("O2 des.", value=0.94, format="%.3f")

# STEP 2: SIMULATION SETTINGS
st.write("#### 2. Potential Sweep Settings")
u_min, u_max = st.select_slider(
    "Select Potential Range (V vs RHE)",
    options=np.round(np.arange(0.0, 4.1, 0.1), 1),
    value=(1.2, 2.3)
)

# STEP 3: EXECUTION
if st.button("Run Kinetics Simulation", type="primary", use_container_width=True):
    model = OERKineticModel([dg1, dg2, dg3, dg4, dg5], site_name)
    u_range = np.linspace(u_min, u_max, 100)
    
    with st.spinner("Solving steady-state coverage..."):
        results = model.solve_coverage(u_range)
    
    # Plotting
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(u_range, results["H2O"], label='*H$_2$O', lw=3)
    ax.plot(u_range, results["OH"], label='*OH', lw=3)
    ax.plot(u_range, results["O"], label='*O', lw=3)
    ax.plot(u_range, results["OOH"], label='*OOH', lw=3)
    ax.plot(u_range, results["star"], label='* (Free site)', linestyle='--', color='gray')
    
    ax.set_xlabel('Potential [V vs RHE]')
    ax.set_ylabel('Surface Coverage [$\Theta$]')
    ax.set_title(f"Surface Evolution on {site_name}")
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    st.pyplot(fig)
    
    with st.expander("View Raw Data Table"):
        st.dataframe(pd.DataFrame(results, index=u_range))

# --- FOOTER ---
st.divider()
if st.button("Complete Module 6 🚀"):
    st.switch_page("pages/08_Module_7.py")