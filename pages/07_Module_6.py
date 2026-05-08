import streamlit as st
import importlib
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import numpy as np
import pandas as pd
import io
from utils.ui_components import (
    module_header, 
    main_content_text, 
    sub_section_header, 
    highlight_box,
    inject_global_css,   
    style_sidebar,      
    render_sidebar_progress 
)

#
# --- 1. GLOBAL STYLING & CONFIG ---
st.set_page_config(
    page_title="Module 6: Kinetics | CMD-ITB", 
    layout="wide"
)
inject_global_css()
style_sidebar()

# 1. DYNAMIC IMPORT
try:
    module_logic = importlib.import_module("utils.07_Module_6")
    OERKineticModel = module_logic.OERKineticModel
except Exception as e:
    st.error(f"Logic Module Error: {e}")

# --- NAVIGATION HEADER ---
module_header("06", "OER Kinetics Simulation", "Modeling reaction kinetics based on Gibbs free energy inputs")  

st.subheader("Kinetics Dashboard")

# SITE IDENTITY
site_name = st.text_input("Active Site Name", value="Ni-Fe Site")

# STEP 1: ENERGETICS
st.write("#### 1. Input Energetics ($\Delta G$ in eV)")
with st.container(border=True):
    d1, d2, d3 = st.columns(3)
    dg1 = d1.number_input("H2O ads.", value=-0.320, format="%.3f")
    dg2 = d2.number_input("OH form.", value=1.320, format="%.3f")
    dg3 = d3.number_input("O form.", value=1.470, format="%.3f")
    dg4 = d1.number_input("OOH form.", value=1.510, format="%.3f")
    dg5 = d2.number_input("O2 des.", value=0.940, format="%.3f")

# STEP 2: SIMULATION SETTINGS
st.write("#### 2. Potential Sweep Settings")
u_min = st.number_input("Min Potential (V)", value=1.2, step=0.1)
u_max = st.number_input("Max Potential (V)", value=2.3, step=0.1)

# STEP 3: EXECUTION
if st.button("Run Kinetics Simulation", type="primary", use_container_width=True):
    model = OERKineticModel([dg1, dg2, dg3, dg4, dg5], site_name)
    u_range = np.linspace(u_min, u_max, 100)
    
    with st.spinner("Solving ODEs and calculating TOF..."):
        results = model.solve_coverage(u_range)
    
    # --- PLOTTING WITH GRIDSPEC ---
    fig = plt.figure(figsize=(16, 7))
    gs = GridSpec(1, 2, figure=fig)
    
    # AX 1: Surface Coverage
    ax0 = fig.add_subplot(gs[0, 0])
    ax0.plot(u_range, results["H2O"], label='*H$_2$O', lw=3)
    ax0.plot(u_range, results["OH"], label='*OH', lw=3)
    ax0.plot(u_range, results["O"], label='*O', lw=3)
    ax0.plot(u_range, results["OOH"], label='*OOH', lw=3)
    ax0.plot(u_range, results["star"], label='* (Free site)', linestyle='--', color='gray')
    ax0.set_xlabel('$\Delta U$ [V]', fontsize=14)
    ax0.set_ylabel('Surface Coverage [$\Theta$]', fontsize=14)
    ax0.set_title("Surface Evolution", fontsize=16, fontweight='bold')
    ax0.legend(fontsize=12)
    ax0.grid(linestyle='--', alpha=0.6)

    # AX 2: TOF Graph (using your provided styling)
    ax1 = fig.add_subplot(gs[0, 1])
    tof_log = np.log10(results["TOF"])
    
    # Custom colors from your snippet
    colors = ["orange","green","blue","red","purple","salmon","pink","cyan","lime","brown","magenta","teal"]
    
    # Plotting logic based on your line-style requirements
    ax1.plot(u_range, tof_log, '-', color=colors[1], label=site_name, lw=4)
    
    # Apply your specific axis limits and labels
    ax1.set_xlim(u_min, u_max)
    ax1.set_ylim(-7, 9)
    ax1.set_ylabel('log$_{10}$(TOF) [site$^{-1}$ s$^{-1}$]', fontsize=20)
    ax1.set_xlabel('$\Delta U$ [V]', fontsize=20)
    ax1.tick_params(axis='both', labelsize=20)
    ax1.grid(linestyle='--')
    ax1.legend(loc="lower right", fontsize=14)
    ax1.set_title("TOF Performance", fontsize=16, fontweight='bold')

    plt.tight_layout()
    st.pyplot(fig)
    
    # --- DOWNLOAD OPTION (330 PPI) ---
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=330, bbox_inches='tight')
    st.download_button("Download High-Res Graph (330 PPI)", buf.getvalue(), "TOF_Coverage_Analysis.png", "image/png")

    with st.expander("View Raw Data Table"):
        st.dataframe(pd.DataFrame(results, index=u_range))

# --- FOOTER ---
st.divider()

col_b, col_n = st.columns([1, 4])

with col_b:
    # Standard Typographic Back Arrow
    if st.button("← Back"):
        st.switch_page("pages/06_Module_5.py")

with col_n:
    # Standard Typographic Forward Arrow with Primary Styling
    if st.button("Complete Module 6 →", type="primary", use_container_width=True):
        st.switch_page("pages/08_Module_7.py")

# Ensure Sidebar remains consistent
render_sidebar_progress(st.session_state.get('progress', 65))