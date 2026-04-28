import streamlit as st
import importlib
import pandas as pd
import plotly.graph_objects as go
import numpy as np

# Dynamic Import
module_logic = importlib.import_module("utils.08_Module_7")
Volcano = module_logic.VolcanoAnalyzer()

st.set_page_config(page_title="Module 7: Volcano Plot", layout="wide")

st.title("08 | Module 7: Volcano Plot")
st.divider()

# --- INPUT SECTION ---
st.write("#### 1. Screening Data Input")
default_data = pd.DataFrame([
    {"Material": "NiFePO", "dG_OH": 1.10, "dG_O": 2.50, "eta_exp": 0.35},
    {"Material": "CoP", "dG_OH": 1.40, "dG_O": 2.90, "eta_exp": 0.45},
])

edited_df = st.data_editor(default_data, num_rows="dynamic", use_container_width=True)

# --- PLOTTING SECTION ---
if st.button("Generate Volcano Plot", type="primary", use_container_width=True):
    processed_df = Volcano.process_screening_data(edited_df)
    
    # Generate Volcano Background Lines
    x_line = np.linspace(0.8, 2.2, 100)
    y_line = Volcano.get_volcano_lines(x_line)
    
    fig = go.Figure()

    # Theoretical Volcano Shape (Negated)
    fig.add_trace(go.Scatter(
        x=x_line, y=y_line, 
        mode='lines', 
        line=dict(color='black', width=2, dash='dot'),
        name='Theoretical Activity Limit'
    ))

    # User Data Points (Negated)
    fig.add_trace(go.Scatter(
        x=processed_df['Descriptor'], 
        y=processed_df['eta_plot'], 
        mode='markers+text',
        text=processed_df['Material'],
        textposition="top center",
        marker=dict(size=14, color='royalblue', symbol='diamond', 
                    line=dict(width=2, color='DarkSlateGrey')),
        name='Your Samples'
    ))

    fig.update_layout(
        xaxis_title="Descriptor [ΔG_O - ΔG_OH] (eV)",
        yaxis_title="Negated Overpotential [-η] (V)",
        template="plotly_white",
        height=600,
        showlegend=True
    )

    st.plotly_chart(fig, use_container_width=True)
    st.info("💡 Note: Overpotential values have been multiplied by -1. The materials closest to the peak are your most active catalysts.")