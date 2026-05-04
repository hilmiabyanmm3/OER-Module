import streamlit as st
import importlib
import io

# 1. LOGIC IMPORTS
module_logic = importlib.import_module("utils.04_Module_3")

# Initialize AdsorbateGenerator in session state
if 'ads_gen' not in st.session_state:
    st.session_state.ads_gen = module_logic.AdsorbateGenerator()

st.set_page_config(page_title="Module 3: Adsorbates", layout="wide")

# --- NAVIGATION HEADER ---
st.title("04 | Module 3: Adsorbate Generator")
col_nav, _ = st.columns([1, 5])
with col_nav:
    if st.button("⬅️ Back to Module 2"):
        st.switch_page("pages/03_Module_2.py")
st.divider()

# --- TABBED INTERFACE ---
tab1, tab2 = st.tabs(["Step 1: Slab Loading & Site Selection", "Step 2: Adsorbate Data Analysis"])

with tab1:
    st.subheader("Structure Setup")
    st.info("Upload your relaxed slab output file to identify active metal sites.")

    uploaded_out = st.file_uploader("Upload Relaxed Slab Output (.out)", type=["out", "log"], key="slab_uploader")

    if uploaded_out:
        content = uploaded_out.getvalue().decode('utf-8', errors='ignore')
        
        if st.session_state.ads_gen.load_slab(content):
            st.success(f"Slab Loaded: {st.session_state.ads_gen.base_atoms.get_chemical_formula()}")
            
            # --- UPDATED SITE FINDING FORM ---
            with st.form("site_finder"):
                st.write("#### Global Site Detection")
                col_m, col_n = st.columns([2, 1])
                
                with col_m:
                    metals = st.multiselect(
                        "Active Elements to Include:", 
                        ["Ni", "Fe", "Co", "Mn"], 
                        default=["Ni", "Fe"]
                    )
                
                with col_n:
                    # Clarified: n is the sum total of all selected metals
                    n_total = st.number_input(
                        "Total Top Atoms (Sum):", 
                        min_value=1, 
                        value=4, 
                        help="Select the top 'n' atoms total from all selected elements combined, based on highest Z-coordinates."
                    )

                if st.form_submit_button("Find Top Sites", type="primary"):
                    # Logic now handles n_total as the combined limit
                    st.session_state.found_sites = st.session_state.ads_gen.find_top_sites(metals, n_total)

    # Render Site Selection results
    if st.session_state.get('found_sites'):
        st.divider()
        st.write(f"### Select Active Sites (Top {len(st.session_state.found_sites)} Metal Atoms Identified)")
        selected_sites = []
        
        for site in st.session_state.found_sites:
            label = f"Site {site['index_qe']} ({site['symbol']}) at Z={site['z_coord']:.2f}"
            if st.checkbox(label, value=True, key=f"site_{site['index_qe']}"):
                selected_sites.append(site)
        
        if st.button("Generate Adsorbate Structures", type="primary"):
            if selected_sites:
                with st.spinner("Generating intermediate coordinates..."):
                    zip_data = st.session_state.ads_gen.build_adsorbates_zip(selected_sites)
                    st.download_button(
                        label="⬇️ Download OER_Adsorbates.zip",
                        data=zip_data,
                        file_name="OER_Adsorbates.zip",
                        mime="application/zip"
                    )
            else:
                st.warning("Please select at least one site to proceed.")

with tab2:
    st.subheader("Results Analysis")
    st.info("Upload the ZIP file containing all your optimized OER intermediate results.")

    if 'ads_analyzer' not in st.session_state:
        st.session_state.ads_analyzer = module_logic.AdsorbateAnalyzer()

    uploaded_results = st.file_uploader("Upload Results ZIP", type="zip", key="results_uploader")

    if uploaded_results:
        if st.button("Extract Energies & Group by Site", type="primary"):
            with st.spinner("Analyzing structural paths..."):
                df_results = st.session_state.ads_analyzer.process_zip(uploaded_results.getvalue())
                
                if not df_results.empty:
                    st.success(f"Successfully processed structures.")
                    df_display = df_results[df_results['Path'] != ""]
                    st.dataframe(
                        df_display[['Step', 'Site', 'Energy (Ry)', 'Termination']].style.format({"Energy (Ry)": "{:.6f}"}), 
                        use_container_width=True
                    )
                    
                    excel_data = st.session_state.ads_analyzer.generate_excel(df_results)
                    st.download_button(
                        label="📊 Download Excel Report",
                        data=excel_data,
                        file_name="oer_energy_report.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                else:
                    st.warning("No valid OER data found. Check folder naming conventions.")

# --- FOOTER ---
st.divider()
if st.button("Complete Module 3 🚀"):
    st.switch_page("pages/05_Module_4.py")