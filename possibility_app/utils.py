import pandas as pd

stim_dat = pd.read_csv('static/stim_data/HMTG_possib_stim.csv', header=0, index_col=0)
stim = stim_dat.loc[stim_dat.trustee == 4]
stim = stim.sample(frac=1, random_state=42).reset_index(drop=True)
stim['trial'] = range(len(stim))
