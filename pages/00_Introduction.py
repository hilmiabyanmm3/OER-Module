import streamlit as st
from utils.ui_components import module_header, main_content_text, sub_section_header, highlight_box, learning_objectives

# --- 1. LAYOUT SETUP ---
left, mid, right = st.columns([1, 4, 1])

with mid:
    # --- 2. HEADER ---
    module_header("01", "Introduction", "Fundamental Concepts & Computational Workflow")

    # --- 3. ABOUT OER ---
    sub_section_header("The Science of Water Splitting", emoji="💡")
    main_content_text("""
        Electrolysis is an environmentally friendly method to produce hydrogen, but cost remains 
        a significant barrier. By utilizing electrical energy—ideally from solar, wind, or tidal 
        sources—we can split water into hydrogen and oxygen gases.
    """)
    
    

    main_content_text("""
        This reaction occurs in an <b>electrolyzer</b> involving two critical half-reactions: 
        the Hydrogen Evolution Reaction (HER) on the cathode and the <b>Oxygen Evolution 
        Reaction (OER)</b> on the anode. Due to its complex elementary steps, OER requires 
        a higher overpotential, making it the primary bottleneck in overall efficiency. 
        Developing catalysts with lower overpotential is essential for viable green 
        hydrogen production<sup>[1]</sup>.
    """)

    highlight_box("""
        <b>Core Objective:</b> Our goal is to measure the <b>Overpotential</b>. 
        A lower overpotential indicates a high-performing material as an <b>Anode</b> catalyst 
        for oxygen evolution.
    """, type="info")

    # --- 4. DICTIONARY (Expander for Focus) ---
    with st.expander("📖 Terminology Dictionary", expanded=False):
        st.markdown("""
        * **Electrolysis:** The process of using electricity to drive a non-spontaneous chemical reaction.
        * **OER (Anode):** The oxidation of water to produce oxygen gas.
        * **HER (Cathode):** The reduction of protons/water to produce hydrogen gas.
        * **Reaction Potential:** The theoretical voltage required for the reaction (1.23V for water splitting).
        * **Overpotential ($\eta$):** The extra voltage required beyond the theoretical value to drive the reaction at a specific rate.
        """)

    # --- 5. COMPUTATIONAL DETAILS & WORKFLOW ---
    st.divider()
    sub_section_header("Computational Strategy", emoji="💻")
    st.write("**Target Material:** Nickel Phosphate ($Ni_2P_2O_7$)")
    
    learning_objectives([
        "Phase 1 (Mod 1-2): Building and optimizing the Bulk and Slab models.",
        "Phase 2 (Mod 3-5): Calculating Adsorption, ZPE, and the Overpotential.",
        "Phase 3 (Mod 6-7): Moving to Kinetics and final Volcano Visualization."
    ])

    # --- 6. DATA & ANALYSIS ---
    sub_section_header("Expected Outputs & Insights", emoji="📊")
    
    col_img1, col_img2, col_img3 = st.columns(3)
    with col_img1:
        st.caption("Gibbs Energy Profile")
        st.write("📈 *Step-by-step energy levels*")
    with col_img2:
        st.caption("Overpotential Analysis")
        st.write("🎯 *Overall performance metric*")
    with col_img3:
        st.caption("Microkinetic Model")
        st.write("⏱️ *Reaction rates and flux*")

    

    # --- 7. EXPERIMENT VS COMPUTATION ---
    with st.expander("🔬 Experimental Comparison"):
        st.write("""
        - **Overpotential:** Computation predicts the intrinsic performance, helping explain experimental observations.
        - **Structure:** Computation tests pristine surfaces to isolate effects, while experiments reveal the impact of defects and surface reconstruction.
        """)

    # --- 8. FOOTNOTES & APPENDIX ---
    st.divider()
    st.markdown("""
        <div style="font-size: 0.85rem; color: #6c757d;">
            <b>References & Appendix</b><br>
            [1] <a href="https://doi.org/10.1016/j.fuel.2024.134183" style="color: #007BFF;">Fuel, 2024. https://doi.org/10.1016/j.fuel.2024.134183</a><br><br>
            <b>Note:</b> All calculations in this module assume standard conditions unless otherwise stated.
        </div>
    """, unsafe_allow_html=True)

    # --- 9. NAVIGATION ---
    if st.button("Proceed to Pre-requisite ➡️", use_container_width=True):
        st.switch_page("pages/01_Pre-requisite.py")