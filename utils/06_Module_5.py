# utils/06_Module_5.py
import pandas as pd

class BottleneckAnalyzer:
    def __init__(self):
        self.step_names = ["H2O -> *OH", "*OH -> *O", "*O -> *OOH", "*OOH -> O2"]

    def identify_bottlenecks(self, plot_data):
        analysis_results = []
        for site_data in plot_data:
            # We look at steps 1 to 4 (Step 0 is the initial water adsorption)
            deltas = site_data['deltaG'][1:] 
            max_val = max(deltas)
            pds_index = deltas.index(max_val)
            
            # Logic for "Prescription"
            prescription = ""
            if pds_index == 2: # *O -> *OOH
                prescription = "O-O bond formation is difficult. Try decreasing oxygen binding strength."
            elif pds_index == 0: # *H2O -> *OH
                prescription = "Water dissociation is slow. Try increasing surface hydrophobicity or metal nucleophilicity."
            else:
                prescription = "General scaling relation bottleneck. Check metal-adsorbate interaction."

            analysis_results.append({
                "Site": site_data['label'],
                "PDS Step": self.step_names[pds_index],
                "Energy Barrier (eV)": max_val,
                "Overpotential (V)": max_val - 1.23,
                "Prescription": prescription,
                "all_deltas": deltas
            })
        return analysis_results