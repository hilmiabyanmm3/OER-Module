import streamlit as st
import importlib
import zipfile

# 1. LOGIC IMPORTS
module_logic = importlib.import_module("utils.04_Module_3")

# Initialize AdsorbateGenerator in session state so it persists across tab switches
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
    st.info("Identify active metal sites for OER intermediates (*H2O, *OH, *O, *OOH).")

    uploaded_zip = st.file_uploader("Upload Slab ZIP (containing .out)", type="zip", key="slab_uploader")

    if uploaded_zip:
        with zipfile.ZipFile(uploaded_zip, 'r') as z:
            out_files = [f for f in z.namelist() if f.endswith(('.out', '.log')) and not '__MACOSX' in f]
            if out_files:
                content = z.read(out_files[0]).decode('utf-8')
                if st.session_state.ads_gen.load_slab(content):
                    st.success(f"Slab Loaded: {st.session_state.ads_gen.base_atoms.get_chemical_formula()}")
                
                    # Site Finding Form
                    with st.form("site_finder"):
                        metals = st.multiselect("Active Elements:", ["Ni", "Fe", "Co", "Mn"], default=["Ni", "Fe"])
                        if st.form_submit_button("Find Top Sites"):
                            st.session_state.found_sites = st.session_state.ads_gen.find_top_sites(metals)

    # Render Site Selection
    if st.session_state.get('found_sites'):
        st.divider()
        st.write("### Select Active Sites")
        selected_sites = []
        # Display checkboxes for identified metal sites
        for site in st.session_state.found_sites:
            label = f"Site {site['index_qe']} ({site['symbol']}) at Z={site['z_coord']:.2f}"
            if st.checkbox(label, value=True, key=f"site_{site['index_qe']}"):
                selected_sites.append(site)
        
        if st.button("Generate Adsorbate Structures", type="primary"):
            if selected_sites:
                with st.spinner("Generating intermediate coordinates..."):
                    zip_data = st.session_state.ads_gen.build_adsorbates_zip(selected_sites)
                    st.download_button("⬇️ Download OER_Adsorbates.zip", zip_data, "OER_Adsorbates.zip")
            else:
                st.warning("Please select at least one site.")

with tab2:
    st.subheader("Results Analysis")
    st.info("Extract energies from your completed OER intermediate optimizations.")

    # Initialize Analyzer if not present
    if 'ads_analyzer' not in st.session_state:
        st.session_state.ads_analyzer = module_logic.AdsorbateAnalyzer()

    uploaded_results = st.file_uploader("Upload Results ZIP", type="zip", key="results_uploader")

    if uploaded_results:
        if st.button("Extract Energies & Group by Site", type="primary", key="extract_btn"):
            with st.spinner("Analyzing structural paths..."):
                df_results = st.session_state.ads_analyzer.process_zip(uploaded_results.getvalue())
                
                if not df_results.empty:
                    st.success(f"Successfully processed {len(df_results)} structures.")
                    
                    # Display table
                    df_display = df_results[df_results['Path'] != ""]
                    st.dataframe(df_display[['Step', 'Site', 'Energy (Ry)', 'Termination']], use_container_width=True)
                    
                    # Downloads
                    c1, c2 = st.columns(2)
                    excel_data = st.session_state.ads_analyzer.generate_excel(df_results)
                    c1.download_button("📊 Download Excel Report", excel_data, "oer_energy_report.xlsx", use_container_width=True)
                else:
                    st.warning("No valid OER data found. Check folder naming (1-h2o, etc).")

# --- FOOTER ---
st.divider()
if st.button("Complete Module 3 🚀"):
    st.switch_page("pages/05_Module_4.py")