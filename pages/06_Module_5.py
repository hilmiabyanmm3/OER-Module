import streamlit as st
import importlib
import pandas as pd
import plotly.express as px

# Dynamic Import
module_logic = importlib.import_module("utils.06_Module_5")
Analyzer = module_logic.BottleneckAnalyzer()

st.set_page_config(page_title="Module 5: Bottleneck Analysis", layout="wide")

st.title("06 | Module 5: Bottleneck Intelligence")

# Check if we have data from Module 4
if 'gibbs_plot_data' not in st.session_state:
    st.warning("⚠️ Please complete the Gibbs Analysis in Module 4 first to see results here.")
else:
    plot_data = st.session_state['gibbs_plot_data']
    results = Analyzer.identify_bottlenecks(plot_data)

    tab1, tab2 = st.tabs(["📊 Bottleneck Heatmap", "💡 Catalyst Prescriptions"])

    with tab1:
        st.subheader("Potential Determining Step (PDS) Heatmap")
        
        # Prepare Heatmap Data
        hm_rows = []
        for r in results:
            row = {"Site": r['Site']}
            for i, val in enumerate(r['all_deltas']):
                row[Analyzer.step_names[i]] = val
            hm_rows.append(row)
        
        df_hm = pd.DataFrame(hm_rows).set_index("Site")
        
        # Plotly Heatmap
        fig = px.imshow(df_hm, 
                        labels=dict(x="Reaction Step", y="Active Site", color="deltaG (eV)"),
                        color_continuous_scale="RdYlGn_r",
                        aspect="auto")
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Darker red cells indicate the largest energy barriers (Bottlenecks).")

    with tab2:
        st.subheader("Insight-Driven Design")
        for res in results:
            with st.expander(f"Analysis for Site: {res['Site']}", expanded=True):
                c1, c2 = st.columns([1, 2])
                c1.metric("Bottleneck Step", res['PDS Step'])
                c1.metric("Overpotential", f"{res['Overpotential (V)']:.2f} V")
                c2.info(f"**Researcher Insight:** {res['Prescription']}")

# --- FOOTER ---
st.divider()
if st.button("Finalize Project & Generate Full Report 🏁"):
    st.balloons()
    st.success("OER Pipeline Processed from A to B!")