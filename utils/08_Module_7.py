# utils/08_Module_7.py
import numpy as np
import pandas as pd

class VolcanoAnalyzer:
    def __init__(self):
        self.theoretical_limit = 1.23 

    def process_screening_data(self, df):
        """Calculates descriptors and applies the -1 multiplier to overpotential."""
        if 'dG_O' in df.columns and 'dG_OH' in df.columns:
            # Descriptor: Delta G_O - Delta G_OH
            df['Descriptor'] = df['dG_O'] - df['dG_OH']
            
            # If 'eta_exp' is provided by the user, we apply the multiplier for the plot
            if 'eta_exp' in df.columns:
                # Detail: Multiplying overpotential by -1 for the Volcano visualization
                df['eta_plot'] = df['eta_exp'] * -1
        return df

    def get_volcano_lines(self, x_range):
        """Generates the 'legs' of the volcano based on negated overpotential."""
        # Standard OER Volcano: eta = max(G_O-G_OH - 1.23, 3.2-(G_O-G_OH) - 1.23)
        # Negated for plot: -eta
        y_vals = []
        for x in x_range:
            eta = max(x - 1.23, (3.2 - x) - 1.23)
            y_vals.append(eta * -1) # Applying the -1 multiplier here too
        return y_vals