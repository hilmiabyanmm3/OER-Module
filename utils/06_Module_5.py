import pandas as pd
import numpy as np
import math
import matplotlib.pyplot as plt
import matplotlib as mpl

class BottleneckAnalyzer:
    def __init__(self):
        self.step_names = ["H2O -> *OH", "*OH -> *O", "*O -> *OOH", "*OOH -> O2"]

    def identify_bottlenecks(self, plot_data):
        analysis_results = []
        for site_data in plot_data:
            # We look at electrochemical steps 2 to 5 (Index 1 to 4 in deltaG)
            deltas = site_data['deltaG'][1:] 
            max_val = max(deltas)
            pds_index = deltas.index(max_val)
            
            prescription = ""
            if pds_index == 2: # *O -> *OOH
                prescription = "O-O bond formation is difficult. Try decreasing oxygen binding strength or using a co-catalyst."
            elif pds_index == 0: # *H2O -> *OH
                prescription = "Water dissociation is slow. Try increasing surface hydrophobicity or metal nucleophilicity."
            elif pds_index == 1: # *OH -> *O
                prescription = "Oxo formation is the barrier. Check if the metal center is too stable in the hydroxyl state."
            else: # *OOH -> O2
                prescription = "Product release is limited. Scaling relations suggest the OOH binding is too weak."

            analysis_results.append({
                "Site": site_data['label'],
                "PDS Step": self.step_names[pds_index],
                "Overpotential (V)": max_val - 1.23,
                "Prescription": prescription
            })
        return analysis_results

class GibbsAnalyzer:
    def __init__(self):
        self.ry_to_ev = 13.605698066
        self.colors = ["orange","green","blue","red","purple","salmon","pink","cyan","lime","brown"] * 3
        self.markers = ["s"]*12 + ["^"]*12 + ["o"]*12

    def _clean_dataframe(self, df):
        if 'Path' in df.columns:
            return df[df['Path'].notna() & (df['Path'] != "")].copy()
        return df.dropna(how='all').copy()

    def calculate_deltas(self, df_energy, df_zpe, G_H2O, G_H2, U):
        df_e = self._clean_dataframe(df_energy)
        df_z = self._clean_dataframe(df_zpe)

        merged = pd.merge(df_e, df_z[['Step', 'Site', 'ZPE (eV)']], on=['Step', 'Site'], how='left')
        merged['ZPE (eV)'] = merged['ZPE (eV)'].fillna(0.0)
        merged['E (eV)'] = merged['Energy (Ry)'] * self.ry_to_ev

        results = []
        G_O2 = 4.92 + 2 * G_H2O - 2 * G_H2
        G_PE = 0.5 * G_H2 

        for site, group in merged.groupby(['Site']):
            def get_val(step_name, col):
                val = group[group['Step'] == step_name][col].values
                return val[0] if len(val) > 0 else None

            E_vals = [get_val('slab', 'E (eV)'), get_val('1-h2o', 'E (eV)'),
                      get_val('2-oh', 'E (eV)'), get_val('3-o', 'E (eV)'), get_val('4-ooh', 'E (eV)')]
            Z_vals = [0.0, get_val('1-h2o', 'ZPE (eV)'), get_val('2-oh', 'ZPE (eV)'),
                      get_val('3-o', 'ZPE (eV)'), get_val('4-ooh', 'ZPE (eV)')]
            
            if None in E_vals: continue

            dg = []
            dg.append(E_vals[1] + Z_vals[1] - (G_H2O + E_vals[0])) # Step 1: Adsorption
            dg.append(E_vals[2] + Z_vals[2] + (G_PE - U) - (E_vals[1] + Z_vals[1])) # Step 2
            dg.append(E_vals[3] + Z_vals[3] + (G_PE - U) - (E_vals[2] + Z_vals[2])) # Step 3
            dg.append(E_vals[4] + Z_vals[4] + (G_PE - U) - G_H2O - (E_vals[3] + Z_vals[3])) # Step 4
            dg.append(E_vals[0] + G_O2 + (G_PE - U) - (E_vals[4] + Z_vals[4])) # Step 5

            overpotential = max(dg[1:]) - 1.23

            levels = [0.0]
            for val in dg: levels.append(levels[-1] + val)
            
            dataX, dataY = [], []
            for i, l in enumerate(levels):
                dataX.extend([2*i, 2*i+1])
                dataY.extend([l, l])

            results.append({
                "label": site[0] if isinstance(site, tuple) else site,
                "deltaG": dg, "overpotential": overpotential,
                "dataX": dataX, "dataY": dataY
            })
        return results

    def create_plot(self, plot_data, title, U_shift=0.0):
        plt.rcParams['font.family'] = 'DejaVu Sans'
        plt.rcParams['axes.linewidth'] = 2
        fig = plt.figure(figsize=(9, 6))
        ax = fig.add_axes([0.1, 0.1, 0.75, 0.8])

        all_shifted_y = []
        for data in plot_data:
            dg = data['deltaG']
            y_levels = [0.0]
            y_levels.append(y_levels[-1] + dg[0])
            for k in range(1, 5):
                y_levels.append(y_levels[-1] + dg[k] - U_shift)
            
            y_plot = []
            for l in y_levels: y_plot.extend([l, l])
            data['temp_y'] = y_plot
            all_shifted_y.extend(y_plot)

        ax.set_ylabel('Gibbs Free Energy (eV)', fontsize=16)
        ax.set_xlabel('Reaction Coordinate', fontsize=16)
        ax.set_xticks([])
        
        if all_shifted_y:
            ax.set_ylim(min(all_shifted_y) - 0.5, max(all_shifted_y) + 1.2)

        istep = ["*+H$_2$O", "*H$_2$O","*OH", "*O", "*OOH", "*+O$_2$"]
        ref_x = plot_data[0]['dataX']
        for i in range(6):
            max_y = max(d['temp_y'][2*i] for d in plot_data)
            ax.text(i*2 + 0.5, max_y + 0.15, istep[i], ha="center", fontsize=12, fontweight='bold')

        for i, data in enumerate(plot_data):
            c = self.colors[i % len(self.colors)]
            m = self.markers[i % len(self.markers)]
            x, y = data['dataX'], data['temp_y']
            
            # Platforms & Connections
            for j in range(5):
                ax.plot([x[2*j+1], x[2*j+2]], [y[2*j+1], y[2*j+2]], color=c, linestyle='--', alpha=0.6)
            for j in range(6):
                line_label = data['label'] if j == 0 else ""
                ax.plot([x[2*j], x[2*j+1]], [y[2*j], y[2*j+1]], color=c, linewidth=4, label=line_label)
                ax.plot(x[2*j]+0.5, y[2*j], marker=m, color=c, markeredgecolor='black', markersize=8)

        ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1), frameon=False, fontsize=12)
        ax.set_title(title, loc='left', fontsize=18, pad=20)
        return fig