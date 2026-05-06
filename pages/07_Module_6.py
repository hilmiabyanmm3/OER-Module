import streamlit as st
import importlib
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

# --- 1. GLOBAL STYLING & CONFIG ---
st.set_page_config(page_title="Module 5: Gibbs Free Energy Graph", layout="wide")
inject_global_css()
style_sidebar()

# --- 2. DYNAMIC IMPORT ---
try:
    module_logic = importlib.import_module("utils.06_Module_5")
    bottleneck_engine = module_logic.BottleneckAnalyzer()
except Exception as e:
    st.error(f"Logic Module Error: {e}")

# --- 3. NAVIGATION HEADER ---
module_header("05", "Gibbs Free Energy Graph", "Visualizing data from previous calculations")

# Define Tabs
tab1, tab2, tab3 = st.tabs(["Step 1: Gibbs Analysis", "Step 2: Gibbs Graph", "Step 3: PDS"])

# --- TAB 1: CALCULATION & INTERACTIVE PLOT ---
with tab1:
    st.subheader("Step 1: Gibbs Free Energy Profile")
    st.info("Combine DFT Energies and ZPE to visualize the OER reaction coordinate.")

    if 'gibbs_engine' not in st.session_state:
        st.session_state.gibbs_engine = module_logic.GibbsAnalyzer()

    c1, c2 = st.columns(2)
    file_e = c1.file_uploader("Upload Energy Summary (Module 4)", type=['xlsx', 'csv'])
    file_z = c2.file_uploader("Upload ZPE Summary (Step 1)", type=['xlsx', 'csv'])

    if file_e and file_z:
        st.divider()
        st.write("#### Thermodynamics Parameters")
        p1, p2, p3 = st.columns(3)
        g_h2o = p1.number_input("G_H2O (eV)", value=-466.4078885915, format="%.10f")
        g_h2 = p2.number_input("G_H2 (eV)", value=-31.8575183992, format="%.10f")
        mat_title = p3.text_input("Material Name", value="OER Catalyst")

        if st.button("Generate Gibbs Profile", type="primary", use_container_width=True):
            df_e = pd.read_excel(file_e) if file_e.name.endswith('xlsx') else pd.read_csv(file_e)
            df_z = pd.read_excel(file_z) if file_z.name.endswith('xlsx') else pd.read_csv(file_z)
            
            results = st.session_state.gibbs_engine.calculate_deltas(df_e, df_z, g_h2o, g_h2, U=0.0)
            
            if results:
                st.session_state.m4_plot_data = results
                st.success("Thermodynamic data ready!")
            else:
                st.error("Data mismatch. Check Site/Step columns.")

    if 'm4_plot_data' in st.session_state:
        st.divider()
        u_slider = st.slider("Applied Potential (U vs RHE)", 0.0, 2.5, 1.23, step=0.01, 
                             help="Real-time shift of electrochemical steps.")
        
        fig = st.session_state.gibbs_engine.create_plot(
            st.session_state.m4_plot_data, 
            title=mat_title, 
            U_shift=u_slider
        )
        st.pyplot(fig)

        # Updated: Download Icon with ↓
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=330, bbox_inches='tight')
        st.download_button("Download Current Plot ↓", buf.getvalue(), "oer_profile.png", "image/png", use_container_width=True)

# --- TAB 2: SUMMARY TABLE ---
with tab2:
    st.subheader("Step 2: Gibbs Graph Summary")
    if 'm4_plot_data' not in st.session_state:
        # Updated: Clean Warning
        st.warning("Please complete the Gibbs Analysis in Step 1 first.")
    else:
        st.write("#### Site Summary & Potential Determining Steps")
        
        table_data = []
        for data in st.session_state.m4_plot_data:
            table_data.append({
                "Site": data["label"],
                "ΔG1": data["deltaG"][0],
                "ΔG2": data["deltaG"][1],
                "ΔG3": data["deltaG"][2],
                "ΔG4": data["deltaG"][3],
                "ΔG5": data["deltaG"][4],
                "Overpotential (V)": data["overpotential"]
            })
        
        df_summary = pd.DataFrame(table_data)

        def highlight_pds(row):
            dg_cols = ['ΔG2', 'ΔG3', 'ΔG4', 'ΔG5']
            styles = [''] * len(row)
            max_val = row[dg_cols].max()
            for i, col in enumerate(row.index):
                if col in dg_cols and row[col] == max_val:
                    styles[i] = 'background-color: #eef6ff; font-weight: bold; color: #007BFF;'
            return styles

        numeric_cols = ["ΔG1", "ΔG2", "ΔG3", "ΔG4", "ΔG5", "Overpotential (V)"]
        st.dataframe(df_summary.style.format("{:.3f}", subset=numeric_cols).apply(highlight_pds, axis=1), use_container_width=True)
        # Updated: Professional Caption Icon
        st.caption("<i class='fa-solid fa-circle-info' style='color:#007BFF;'></i> Blue highlight indicates the Potential Determining Step (PDS).", unsafe_allow_html=True)

# --- TAB 3: INSIGHTS ---
with tab3:
    st.subheader("Step 3: Bottleneck Analysis (PDS)")
    if 'm4_plot_data' not in st.session_state:
        st.warning("Please complete the Gibbs Analysis in Step 1 first.")
    else:
        analysis_results = bottleneck_engine.identify_bottlenecks(st.session_state.m4_plot_data)
        
        st.subheader("Insight-Driven Design")
        for res in analysis_results:
            # Updated: Cleaner Expander Label with Font Awesome
            with st.expander(f"Analysis for Site: {res['Site']}", expanded=True):
                c1, c2 = st.columns([1, 2])
                c1.metric("PDS Step", res['PDS Step'])
                c1.metric("Overpotential", f"{res['Overpotential (V)']:.2f} V")
                c2.info(f"**Researcher Insight:** {res['Prescription']}")

# --- FOOTER ---
st.divider()
col_b, col_n = st.columns([1, 4])
with col_b:
    # Updated: Back Arrow
    if st.button("← Back"):
        st.switch_page("pages/05_Module_4.py")
with col_n:
    # Updated: Forward Arrow
    if st.button("Complete Module 5 →", use_container_width=True):
        st.switch_page("pages/07_Module_6.py")

render_sidebar_progress(st.session_state.get('progress', 65))