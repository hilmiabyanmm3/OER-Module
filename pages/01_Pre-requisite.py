import streamlit as st
from utils.ui_components import module_header, main_content_text, sub_section_header, highlight_box

# --- 1. LAYOUT SETUP ---
left, mid, right = st.columns([1, 4, 1])

with mid:
    # --- 2. HEADER ---
    module_header("PRE", "Pre-requisite", "Essential tools and resources for OER modeling")

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
    
    # Updated Research-Focused Tip
    highlight_box("""
        <b>Tip:</b> Always record the unique <b>Material ID (mp-id)</b> of your bulk structure. 
        This 'fingerprint' ensures your research is reproducible and allows you to 
        quickly cross-reference thermodynamic properties later.
    """, type="info")

    # --- 4. VISUALIZATION (VESTA) ---
    sub_section_header("2. Model Visualization", emoji="💎")
    main_content_text("""
        <b>VESTA</b> (Visualization for Electronic and Structural Analysis) is required 
        for inspecting our 3D crystal structures, verifying slab cuts, and 
        visualizing electron density.
    """)
    st.link_button("Download VESTA", "https://www.jp-minerals.org/vesta/en/download.html")

    # --- 5. DOWNLOAD INPUT FILES ---
    sub_section_header("3. Download Input Files", emoji="📁")
    main_content_text("""
        Download the specific input templates, pseudo-potentials, and reference data 
        required for the <b>NiFePO</b> OER simulation modules.
    """)
    
    st.link_button("Download Input Files", "https://drive.google.com/drive/folders/1YgqMfzjpEIW3pUAWATGuSstM95r9pO8r?usp=sharing")

    # --- 6. READINESS CHECK ---
    st.divider()
    sub_section_header("Readiness Check", emoji="✅")
    
    ready = st.checkbox("I have setup my Pre-requisite and downloaded the necessary files.")
    
    if ready:
        st.success("Pre-requsite setup complete! You are ready to begin.")
        if st.button("Proceed to Module 1: Bulk Setup ➡️", use_container_width=True):
            st.switch_page("pages/02_Module_1.py")
    else:
        st.warning("Please finalize your pre-requisite before proceeding.")