import streamlit as st
from utils.ui_components import module_header, main_content_text, sub_section_header, highlight_box

# 1. GLOBAL CONFIGURATION
st.set_page_config(
    page_title="OER Research Portal | CMD-ITB",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. SESSION STATE INITIALIZATION
if 'progress' not in st.session_state:
    st.session_state['progress'] = 0

# 3. MAIN UI LAYOUT
left, mid, right = st.columns([1, 4, 1])

with mid:
    module_header("HOME", "OER Research Module", "Theoretical & Computational Learning Path")

    main_content_text("""
        The <b>Oxygen Evolution Reaction (OER)</b> is a flagship computational-material 
        research topic at <b>CMD-ITB</b>. This course bridges the gap between 
        theoretical surface science and high-fidelity computational modeling.
    """)
    
    sub_section_header("Why OER?", emoji="🔬")
    st.success("""
    - **Experimentalists:** Deepen your understanding of atomic physics and reaction intermediates.
    - **Computationalists:** Master a rigorous, publication-ready workflow for catalytic systems.
    - **Enthusiasts:** Explore material science from first-principles theory to actionable insights.
    """)

    st.divider()

    # Learning Outcomes
    sub_section_header("What you can get from this module", emoji="🎁")
    col_a, col_b = st.columns(2)
    with col_a:
        main_content_text("🚀 <b>Express Learning:</b> Master a 12-month workflow in just 12 hours.")
        main_content_text("📊 <b>Tool Proficiency:</b> Expert use of VASP, ASE, and Quantum Espresso.")
    with col_b:
        main_content_text("🎓 <b>Full Research Cycle:</b> Complete an end-to-end project across 7 modules.")
        main_content_text("🗣️ <b>2-Way Mentorship:</b> Direct consultation with lab instructors.")

    st.divider()

    # NEW UPDATED MODULE STRUCTURE
    sub_section_header("Course Curriculum", emoji="📑")
    
    # Using columns to show a clean curriculum map
    cur1, cur2 = st.columns(2)
    with cur1:
        st.markdown("""
        **Phase 1: Material Foundations**
        * **Module 1:** Bulk Selection & Variation
        * **Module 2:** Slab Optimization & Surface Energy
        * **Module 3:** Adsorbate Modeling & ZPE
        """)
    with cur2:
        st.markdown("""
        **Phase 2: Thermodynamic & Kinetic Insights**
        * **Module 4:** Gibbs Free Energy Landscape
        * **Module 5:** Overpotential Analysis
        * **Module 6:** Microkinetic Modeling
        * **Module 7:** Data Visualization - Volcano Graphs
        """)

    # Call to Action
    st.divider()
    highlight_box("Ready to transform your understanding of atomic surface science?", type="success")
    
    if st.button("Start Pre-requisite ➡️", use_container_width=True):
        st.switch_page("pages/01_Pre-requisite.py")

# 4. SIDEBAR PROGRESS
st.sidebar.header("Overall Progress")
st.sidebar.progress(st.session_state['progress'])
st.sidebar.info("Begin with Module 1 to establish your Bulk model.")