import streamlit as st
import importlib
import pandas as pd
import plotly.graph_objects as go
import numpy as np
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
st.set_page_config(
    page_title="Module 7: Volcano Plot | CMD-ITB", 
    layout="wide"
)
inject_global_css()
style_sidebar()

# --- 2. DYNAMIC IMPORT ---
try:
    module_logic = importlib.import_module("utils.08_Module_7")
    Volcano = module_logic.VolcanoAnalyzer()
except ImportError:
    st.error("Could not find the utility module: utils.08_Module_7")
    st.stop()

# --- 3. NAVIGATION HEADER ---
module_header("07", "Volcano Plot", "Scaling Relations & Activity Screening")

# --- 4. INPUT SECTION ---
sub_section_header("Screening Data Input", icon_class="fa-solid fa-file-import")

main_content_text("""
    To generate the Volcano plot, upload your compiled results from previous modules. 
    The script will use scaling relations to calculate the theoretical activity limit.
""")

highlight_box("""
    <b>Required Format:</b> Your file must contain the following columns: 
    <code>Material</code>, <code>dG_OH</code>, <code>dG_O</code>, and <code>eta_exp</code> (Experimental Overpotential).
""", type="info")

uploaded_file = st.file_uploader("Upload Screening Data (Excel or CSV)", type=['xlsx', 'csv'])

if uploaded_file:
    # Data Loading
    if uploaded_file.name.endswith('xlsx'):
        input_df = pd.read_excel(uploaded_file)
    else:
        input_df = pd.read_csv(uploaded_file)

    with st.expander("Preview Uploaded Dataset", expanded=False):
        st.dataframe(input_df, use_container_width=True)

    # --- 5. PLOTTING SECTION ---
    if st.button("Generate Volcano Plot", type="primary", use_container_width=True):
        try:
            processed_df = Volcano.process_screening_data(input_df)
            
            # Generate Theoretical Volcano Background
            x_line = np.linspace(0.8, 2.2, 100)
            y_line = Volcano.get_volcano_lines(x_line)
            
            fig = go.Figure()

            # Background: Theoretical Limit
            fig.add_trace(go.Scatter(
                x=x_line, y=y_line, 
                mode='lines', 
                line=dict(color='#6c757d', width=2, dash='dot'),
                name='Theoretical Activity Limit'
            ))

            # Foreground: Research Samples
            fig.add_trace(go.Scatter(
                x=processed_df['Descriptor'], 
                y=processed_df['eta_plot'], 
                mode='markers+text',
                text=processed_df['Material'],
                textposition="top center",
                marker=dict(size=14, color='#007BFF', symbol='diamond', 
                            line=dict(width=2, color='white')),
                name='Calculated Samples'
            ))

            fig.update_layout(
                xaxis_title="Descriptor [ΔG_O - ΔG_OH] (eV)",
                yaxis_title="Negated Overpotential [-η] (V)",
                template="plotly_white",
                height=600,
                font=dict(family="Inter", size=14),
                margin=dict(l=40, r=40, t=40, b=40),
                xaxis=dict(range=[0.8, 2.2], gridcolor='#f0f2f6'),
                yaxis=dict(gridcolor='#f0f2f6')
            )

            st.plotly_chart(fig, use_container_width=True)
            
            st.success("Volcano plot generated successfully!")
            
            st.markdown(f"""
                <div style="background-color: #eef6ff; padding: 15px; border-radius: 8px; border-left: 5px solid #007BFF; margin-top: 20px;">
                    <i class="fa-solid fa-lightbulb" style="color: #007BFF; margin-right: 8px;"></i>
                    <b>Researcher Insight:</b> The Y-axis represents negated overpotential ($- \eta$). 
                    Materials closer to the peak of the dashed line demonstrate optimal binding energy 
                    and theoretically higher catalytic activity.
                </div>""", unsafe_allow_html=True)

        except Exception as e:
            st.error(f"Error processing data: {e}")
            st.warning("Please check if your columns match: Material, dG_OH, dG_O, eta_exp")

else:
    st.info("Please upload a screening dataset to begin the volcano analysis.")

# --- 6. FOOTER & COMPLETION ---
st.divider()

col_b, col_n = st.columns([1, 4])

with col_b:
    if st.button("← Back"):
        st.switch_page("pages/07_Module_6.py")

with col_n:
    if st.button("Finish Research Workflow →", type="primary", use_container_width=True):
        st.balloons()
        st.success("Course Completed!")
        st.markdown("""
            <div style="background-color: #ffffff; padding: 25px; border-radius: 12px; border: 1px solid #f0f2f6; box-shadow: 0 4px 12px rgba(0,0,0,0.05); text-align: center;">
                <i class="fa-solid fa-graduation-cap" style="color: #007BFF; font-size: 2.5rem; margin-bottom: 15px;"></i>
                <h3 style="margin: 0; color: #1a1c1e;">OER Workflow Mastery</h3>
                <p style="color: #6c757d; margin: 15px 0;">
                    You have successfully navigated the end-to-end computational pipeline for Oxygen Evolution Reaction research. 
                    Your results are now ready for publication-level discussion.
                </p>
                <hr style="border: 0; border-top: 1px solid #f0f2f6; margin: 20px 0;">
                <p style="font-size: 0.9rem; color: #3e444b;"><b>CMD-ITB Computational Materials Design Lab</b></p>
            </div>
        """, unsafe_allow_html=True)

# Final Progress Update
render_sidebar_progress(100)