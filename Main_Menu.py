import streamlit as st
import importlib

# 1. IMPORT UI COMPONENTS
from utils.ui_components import (
    module_header, 
    main_content_text, 
    sub_section_header, 
    highlight_box,
    inject_global_css,   
    style_sidebar,      
    render_sidebar_progress 
)

# 2. GLOBAL CONFIGURATION
st.set_page_config(
    page_title="OER Learning Module | CMD-ITB",
    # Updated: Branded Blue DNA Icon
    page_icon="https://img.icons8.com/?size=100&id=vtLGHdmfoSt8&format=png&color=000000", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

inject_global_css()
style_sidebar()

# 3. SESSION STATE INITIALIZATION
if 'progress' not in st.session_state:
    st.session_state['progress'] = 0

# 4. DEFINE PAGE FUNCTIONS
def show_home():
    """Renders the landing page with a tighter top margin and snappier animation."""
    
    # 1. INJECT TUNED CSS
    st.markdown("""
        <style>
            /* Refined Typing Animation: 2s duration, 15 steps */
            @keyframes typing { from { width: 0 } to { width: 100% } }
            @keyframes blink-caret { from, to { border-color: transparent } 50% { border-color: #007BFF; } }

            .typewriter h1 {
              color: #1a1c1e;
              font-family: 'Inter', sans-serif;
              overflow: hidden;
              border-right: .15em solid #007BFF;
              white-space: nowrap;
              margin: 0 auto;
              letter-spacing: -0.04em;
              animation: typing 2s steps(15, end), blink-caret .75s step-end infinite;
              font-size: 3.5rem;
              font-weight: 800;
            }

            /* The Adjusted Container */
            .main-hero {
                display: flex;
                flex-direction: column;
                justify-content: flex-start; /* Pulls content toward the top */
                align-items: center;        /* Keeps it horizontally centered */
                padding-top: 8vh;           /* Adjust this value to move text higher or lower */
                min-height: 45vh;           /* Reduced container height */
                text-align: center;
            }
            
            .hero-subtitle {
                font-size: 1.25rem; 
                color: #6c757d; 
                margin-top: 15px; 
                margin-bottom: 35px; 
                line-height: 1.6;
                max-width: 600px;
            }
        </style>
    """, unsafe_allow_html=True)

    # 2. RENDER THE HERO
    st.markdown("""
        <div class="main-hero">
            <div style="margin-bottom: 20px;">
                <i class="fa-solid fa-microscope" style="color: #007BFF; font-size: 4rem; opacity: 0.9;"></i>
            </div>
            <div class="typewriter">
                <h1>OER Learning Module</h1>
            </div>
            <p class="hero-subtitle">
                The flagship computational-material research module at <b>CMD-ITB</b>.<br>
                Bridging theoretical surface science with high-fidelity modeling.
            </p>
        </div>
    """, unsafe_allow_html=True)

    # 3. ACTION BUTTONS
    _, btn_mid, _ = st.columns([1, 2, 1])
    with btn_mid:
        btn_col1, btn_col2 = st.columns(2)
        with btn_col1:
            if st.button("Start Workflow →", type="primary", use_container_width=True):
                st.switch_page("pages/01_Pre-requisite.py")
        with btn_col2:
            st.link_button(
                "Star on GitHub", 
                "https://github.com/hilmiabyanmm3/OER-Module", 
                use_container_width=True
            )

    # 4. FOOTER
    st.markdown("""
        <div style="text-align: center; margin-top: 40px; padding: 20px; border-top: 1px solid #f0f2f6;">
            <p style="font-size: 0.85rem; color: #adb5bd;">
                © 2026 Computational Materials Design Lab - ITB
            </p>
        </div>
    """, unsafe_allow_html=True)

# 5. DEFINE NAVIGATION STRUCTURE
home_page = st.Page(show_home, title="Home", default=True)
pre_req   = st.Page("pages/01_Pre-requisite.py", title="Pre-requisite")
intro     = st.Page("pages/00_Introduction.py", title ="Introduction")
mod1      = st.Page("pages/02_Module_1.py", title="Module 1: Bulk")
mod2      = st.Page("pages/03_Module_2.py", title="Module 2: Surface")
mod3      = st.Page("pages/04_Module_3.py", title="Module 3: Adsorbate")
mod4      = st.Page("pages/05_Module_4.py", title="Module 4: Vibration")
mod5      = st.Page("pages/06_Module_5.py", title="Module 5: Gibbs Free Energy")
mod6      = st.Page("pages/07_Module_6.py", title="Module 6: Microkinetic")
mod7      = st.Page("pages/08_Module_7.py", title="Module 7: Volcano Graphs")

pg = st.navigation({
    "Portal": [home_page, intro, pre_req],
    "OER Modeling Modules": [mod1, mod2, mod3, mod4, mod5, mod6, mod7]
})

# 6. RENDER SIDEBAR PROGRESS
render_sidebar_progress(st.session_state['progress'])

# 7. RUN NAVIGATION
pg.run()