import pandas as pd
import matplotlib.pyplot as plt
import sys
from icecream import ic

experiment = sys.argv[1]
status = ['completed', 'running', 'planned']
colors = ['#000000', '#009900', '#FF9999']
url = "https://raw.githubusercontent.com/WCRP-CORDEX/simulation-status/main/CMIP6_downscaling_plans.csv"

def get_ymax(exp):
  if exp.startswith('ssp'):
    return(150)
  elif exp.startswith('hist'):
    return(60)
  elif exp.startswith('eval'):
    return(18)
  else:
    return(None)

df = pd.read_csv(url)
df[['domain', 'resolution']] = df['domain'].str.split('-', expand = True)
filtered_df = df[~df['experiment'].isna() & df['experiment'].str.startswith(experiment) & ~df['comments'].str.match('#ESD', na = False)].query('status in @status')
status_counts = filtered_df.groupby(['domain', 'status']).size().unstack(fill_value=0)
status_counts = status_counts[status]
status_counts = status_counts.loc[status_counts.sum(axis=1).sort_values(ascending=False).index]
ic(status_counts)
ic(status_counts.sum(axis=1))
status_counts.plot(kind='bar', stacked=True, figsize=(6, 4), color=colors)
ax = plt.gca()
ax.set_ylim([0, get_ymax(experiment)])
plt.xlabel('')
plt.ylabel('Total number of simulations')
plt.title(f'Simulations by CORDEX domain ({experiment.upper()})')
plt.legend(title='Status', loc='upper right')
plt.tight_layout()
plt.savefig(f'docs/CORDEX_CMIP6_global_progress__{experiment.upper()}.png', bbox_inches='tight')

