import streamlit as st
from utils.ui_components import module_header, main_content_text, sub_section_header, highlight_box

# --- 1. LAYOUT SETUP ---
left, mid, right = st.columns([1, 4, 1])

with mid:
    # --- 2. HEADER ---
    module_header("PRE", "Pre-requisite", "Essential tools and libraries for OER modeling")

    main_content_text("""
        To ensure a smooth transition from theory to computation, please verify that your 
        local workstation is equipped with the following software and data access. 
        These tools will be used throughout the 7 modules.
    """)

    # --- 3. DATA SOURCE (Materials Project) ---
    sub_section_header("1. Bulk Data Source", emoji="🌐")
    main_content_text("""
        We will use the <b>Materials Project</b> database to obtain the initial 
        crystal structures for our Nickel Phosphate models.
    """)
    st.link_button("Access Materials Project", "https://next-gen.materialsproject.org/materials")
    
    highlight_box("""
        <b>Tip:</b> Make sure to register for an account to obtain your <b>API Key</b>, 
         which allows you to download structures directly via Python.
    """, type="info")

    # --- 4. VISUALIZATION (VESTA) ---
    sub_section_header("2. Model Visualization", emoji="💎")
    main_content_text("""
        <b>VESTA</b> (Visualization for Electronic and Structural Analysis) is required 
        for inspecting our 3D crystal structures, verifying slab cuts, and 
        visualizing electron density.
    """)
    st.link_button("Download VESTA", "https://www.jp-minerals.org/vesta/en/download.html")

    # --- 5. PYTHON LIBRARIES ---
    sub_section_header("3. Python Libraries", emoji="🐍")
    main_content_text("""
        Ensure you have a working Python environment (3.9+) with the following 
        libraries installed:
    """)
    
    st.code("""
# Install the core libraries via terminal
pip install ase matplotlib
    """, language="bash")

    st.markdown("""
    * **ASE (Atomic Simulation Environment):** For structural manipulation and DFT interfacing.
    * **Matplotlib:** For generating publication-quality energy profiles and graphs.
    """)

    # --- 6. READINESS CHECK ---
    st.divider()
    sub_section_header("Readiness Check", emoji="✅")
    
    ready = st.checkbox("I have installed the libraries and downloaded VESTA.")
    
    if ready:
        st.success("Environment setup complete! You are ready to begin.")
        if st.button("Proceed to Module 1: Downloading Bulk ➡️", use_container_width=True):
            st.switch_page("pages/02_Module_1.py")
    else:
        st.warning("Please finalize your environment setup before proceeding.")