# pages/05_Module_4.py
import streamlit as st
import importlib
import pandas as pd
from utils.ui_components import (
    module_header, 
    inject_global_css,   
    style_sidebar,      
    render_sidebar_progress 
)

# --- 1. CONFIGURATION & STYLING ---
st.set_page_config(
    page_title="Module 4: ZPE & Vibrations | CMD-ITB", 
    page_icon="https://img.icons8.com/?size=100&id=vtLGHdmfoSt8&format=png&color=000000",
    layout="wide"
)
inject_global_css()
style_sidebar()

# --- 2. BACKEND CONNECTION ---
try:
    mod_logic = importlib.import_module("utils.05_Module_4")
    ZPE_Gen = mod_logic.ZPEManager()
    ZPE_Ana = mod_logic.ZPEAnalyzer()
except Exception as e:
    st.error(f"Logic Module Error: {e}")

# --- 3. SESSION STATE INITIALIZATION ---
if 'boundary_idx' not in st.session_state:
    st.session_state.boundary_idx = 71
if 'excel_bytes' not in st.session_state:
    st.session_state.excel_bytes = None
if 'log_text' not in st.session_state:
    st.session_state.log_text = ""
if 'overwrite_count' not in st.session_state:
    st.session_state.overwrite_count = 0

module_header("04", "Vibrational Analysis", "Adsorbate vibration and Zero-Point Energy (ZPE) calculations")

# --- GLOBAL CONFIGURATION CONTAINER ---
with st.container(border=True):
    st.markdown("### ⚙️ Adsorbate Vibration Boundary Configuration")
    st.info(
        "**Boundary Index Rule:** Atoms with index **≤ Boundary Index** will **NOT** be vibrated (fixed slab/substrate). "
        "Atoms with index **> Boundary Index** will be vibrated (surface adsorbates). "
        "Configuring this once applies it universally to all folders."
    )
    st.session_state.boundary_idx = st.number_input(
        "Atom Boundary Index",
        min_value=0,
        value=int(st.session_state.boundary_idx),
        step=1,
        help="Example: If set to 71, atoms 1 through 71 remain fixed; atoms 72 and above will receive finite displacements."
    )

# --- TABBED WORKFLOW ---
tab1, tab2, tab3 = st.tabs([
    "Step 1: Recursive Displacement Generator", 
    "Step 2: ZPE & Mode Extractor",
    "Audit Log & Excel History"
])

# ==========================================
# TAB 1: DISPLACEMENT GENERATOR
# ==========================================
with tab1:
    st.subheader("Batch Finite Displacement Generator")
    st.markdown(
        "Upload a `.zip` file containing subfolders with `PW.in` and `PW.out` (e.g., `FeN4G_10A/`). "
        "The system generates `PWINPUT_atm*` displacement files, `GEOM.xyz`, and initializes `Vibration_Analysis.xlsx`."
    )

    uploaded_zip = st.file_uploader(
        "Upload Structure Calculations Archive (.zip)",
        type=["zip"],
        key="batch_disp_zip"
    )

    if uploaded_zip:
        if st.button("Generate Finite Displacements", type="primary", use_container_width=True):
            with st.spinner("Scanning folders, writing displacements, and building Excel registry..."):
                final_zip, new_excel, updated_log, count = ZPE_Gen.process_batch_zip(
                    uploaded_zip.getvalue(),
                    st.session_state.boundary_idx,
                    st.session_state.excel_bytes,
                    st.session_state.log_text,
                    st.session_state.overwrite_count
                )
                
                # Persist updated tracking state
                st.session_state.excel_bytes = new_excel
                st.session_state.log_text = updated_log
                st.session_state.overwrite_count = count

                if final_zip:
                    st.success("Finite displacements and tracking registry created successfully!")
                    c_d1, c_d2 = st.columns(2)
                    with c_d1:
                        st.download_button(
                            label="Download Displaced Inputs ZIP ↓",
                            data=final_zip,
                            file_name="displacement_calculations.zip",
                            mime="application/zip",
                            use_container_width=True
                        )
                    with c_d2:
                        st.download_button(
                            label="Download Vibration_Analysis.xlsx ↓",
                            data=st.session_state.excel_bytes,
                            file_name="Vibration_Analysis.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        )

# ==========================================
# TAB 2: ZPE EXTRACTOR
# ==========================================
with tab2:
    st.subheader("Step 2: ZPE & Frequency Data Extractor")
    st.markdown(
        "Upload the `.zip` archive containing completed force logs (`LOG_atm*` or `PWINPUT_atm*.out`). "
        "The Hessian will be solved, computing the Zero-Point Energy (ZPE) and vibrational modes."
    )

    completed_zip = st.file_uploader(
        "Upload Completed Calculation Logs (.zip)", 
        type=["zip"], 
        key="zpe_results_zip"
    )

    if completed_zip:
        if st.button("Extract Forces & Calculate ZPE", type="primary", use_container_width=True):
            with st.spinner("Extracting forces, solving dynamical matrix, and evaluating frequencies..."):
                df_results, new_excel, updated_log, count = ZPE_Ana.process_extraction_zip(
                    completed_zip.getvalue(),
                    st.session_state.boundary_idx,
                    st.session_state.excel_bytes,
                    st.session_state.log_text,
                    st.session_state.overwrite_count
                )

                st.session_state.excel_bytes = new_excel
                st.session_state.log_text = updated_log
                st.session_state.overwrite_count = count

                if not df_results.empty:
                    st.success("Calculations complete! Results updated.")
                    st.dataframe(
                        df_results.style.format({
                            "Energy": "{:.6f}",
                            "ZPE": "{:.4f}"
                        }, na_rep="-"),
                        use_container_width=True
                    )
                    st.download_button(
                        label="Download Updated Vibration_Analysis.xlsx ↓",
                        data=st.session_state.excel_bytes,
                        file_name="Vibration_Analysis.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                else:
                    st.error("No valid force output logs could be parsed from the archive.")

# ==========================================
# TAB 3: AUDIT & LOG HISTORY
# ==========================================
with tab3:
    st.subheader("Audit Log & Version Control")
    st.caption("Tracks previous calculations and logs modifications made to the tracking Excel file.")
    
    if st.session_state.log_text:
        st.text_area("Audit History Log (excel_backup_log.txt)", value=st.session_state.log_text, height=300)
        st.download_button(
            label="Download Log File (excel_backup_log.txt) ↓",
            data=st.session_state.log_text,
            file_name="excel_backup_log.txt",
            mime="text/plain",
            use_container_width=True
        )
    else:
        st.info("No prior overwrites recorded. The log file will be populated if existing records are updated.")

# --- FOOTER NAVIGATION ---
st.divider()
col_b, col_n = st.columns([1, 4])

with col_b:
    if st.button("← Back"):
        st.switch_page("pages/04_Module_3.py")

with col_n:
    if st.button("Complete Module 4 →", type="primary", use_container_width=True):
        st.switch_page("pages/06_Module_5.py")

render_sidebar_progress(st.session_state.get('progress', 55))