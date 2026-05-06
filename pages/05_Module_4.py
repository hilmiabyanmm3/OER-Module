import streamlit as st
import importlib
import io
import zipfile
import pandas as pd
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
st.set_page_config(
    page_title="Module 4: ZPE & Vibrations | CMD-ITB", 
    layout="wide"
)
inject_global_css()
style_sidebar()

# --- 2. DYNAMIC IMPORT ---
try:
    module_logic = importlib.import_module("utils.05_Module_4")
    ZPE = module_logic.ZPEManager()
except Exception as e:
    st.error(f"Logic Module Error: {e}")

# --- 3. NAVIGATION HEADER ---
module_header("04", "Vibrational Analysis", "Adsorbate vibration and Zero-Point Energy (ZPE) calculations")


# --- 4. TABBED INTERFACE ---
tab1, tab2 = st.tabs(["Step 1: Displacement Generator", "Step 2: Frequency Extraction"])

with tab1:
    st.subheader("Displacement Generator")
    st.write("Upload a ZIP containing relaxed OER outputs. The system will automatically detect the adsorbate type (H2O, OH, O, or OOH) and generate 6 displacements per adsorbate atom.")

    with st.container(border=True):
        c1, c2 = st.columns(2)
        with c1:
            uploaded_zip = st.file_uploader("Upload Adsorbate Results ZIP", type=["zip"], key="batch_zpe_zip")
        with c2:
            uploaded_template = st.file_uploader("Upload QE Template", type=["in", "txt"], key="batch_template")

        if uploaded_zip and uploaded_template:
            if st.button("Generate Batch Displacements", type="primary", use_container_width=True):
                template_text = uploaded_template.getvalue().decode("utf-8")
                
                with st.spinner("Processing ZIP and mapping adsorbates..."):
                    final_zip = ZPE.process_batch_zip(uploaded_zip.getvalue(), template_text)
                    
                    if final_zip:
                        st.success("Batch generation complete!")
                        # Updated: Professional Download Label
                        st.download_button(
                            label="Download All Displaced Inputs (ZIP) ↓",
                            data=final_zip,
                            file_name="batch_zpe_inputs.zip",
                            mime="application/zip",
                            use_container_width=True
                        )
                    else:
                        st.error("No valid OER .out files found in the ZIP.")

with tab2:
    st.subheader("Step 2: ZPE Data Extractor")
    st.write("Extract forces from your displacement calculations to obtain the vibrational frequencies and zero-point energies. ")

    uploaded_zpe_zip = st.file_uploader("Upload Completed ZPE ZIP (containing .out logs)", type="zip", key="zpe_results")
    
    if uploaded_zpe_zip:
        if 'zpe_analyzer' not in st.session_state:
             st.session_state.zpe_analyzer = module_logic.ZPEAnalyzer()

        if st.button("Calculate ZPE & Frequencies", type="primary", use_container_width=True):
            with st.spinner("Solving Hessian and extracting Zero-Point Energies..."):
                df_zpe = st.session_state.zpe_analyzer.process_zip(uploaded_zpe_zip.getvalue())
                
                if not df_zpe.empty:
                    st.success(f"Calculated ZPE for {len(df_zpe)} structures.")
                    df_display = df_zpe.dropna(subset=['Site'])
                    st.dataframe(df_display[['Step', 'Site', 'ZPE (eV)']].style.format({"ZPE (eV)": "{:.3f}"}), use_container_width=True)
                    
                    excel_data = st.session_state.zpe_analyzer.generate_excel(df_zpe)
                    # Updated: Professional Excel Download Label
                    st.download_button(
                        label="Download ZPE Results (Excel) ↓", 
                        data=excel_data, 
                        file_name="ZPE_Results.xlsx",
                        use_container_width=True
                    )
                else:
                    st.error("Extraction failed. Ensure folder structure/filenames are correct.")

# --- 5. FOOTER NAVIGATION ---
st.divider()
col_b, col_n = st.columns([1, 4])

with col_b:
    # Standard Typographic Back Arrow
    if st.button("← Back"):
        st.switch_page("pages/04_Module_3.py")

with col_n:
    # Standard Typographic Forward Arrow with Primary Styling
    if st.button("Complete Module 4 →", type="primary", use_container_width=True):
        st.switch_page("pages/06_Module_5.py")

# --- 6. SIDEBAR PROGRESS ---
render_sidebar_progress(st.session_state.get('progress', 55))