import pandas as pd
import matplotlib.pyplot as plt
import sys
from icecream import ic

experiment = sys.argv[1]
mip_era = sys.argv[2]
if mip_era == 'CMIP5':
  url = "https://raw.githubusercontent.com/WCRP-CORDEX/simulation-status/main/docs/CORDEX_CMIP5_status.csv"
else:
  url = 'https://raw.githubusercontent.com/WCRP-CORDEX/simulation-status/main/CMIP6_downscaling_plans.csv'
  url = 'CMIP6_downscaling_plans.csv'

cordex_domains = ['SAM', 'CAM', 'NAM', 'EUR', 'MED', 'MENA', 'AFR', 'WAS', 'CAS', 'EAS', 'SEA', 'AUS', 'ANT', 'ARC']
colors = {
    'published': '#3399FF',
    'completed': '#000000',
    'running': '#009900',
    'planned': '#FF9999'
}
status = colors.keys()

def get_ymax(exp):
  if exp.startswith('ssp'):
    return(125)
  elif exp.startswith('hist'):
    return(60)
  elif exp.startswith('eval'):
    return(25)
  else:
    return(None)

df = pd.read_csv(url)
df[['domain', 'resolution']] = df['domain_id'].str.split('-', expand=True)
if mip_era == 'CMIP5':
  df['comments'] = ''  # Just to make the comments column exist
  df = df[df['resolution'].notna()].query('~resolution.str.endswith("i")')  # avoid double-counting DOM-XXi sims
filtered_df = df[
    ~df['driving_experiment_id'].isna()
   & df['driving_experiment_id'].str.startswith(experiment)
  & ~df['comments'].str.match('#ESD', na=False)
].query('status in @status')

status_counts = filtered_df.groupby(['domain', 'status']).size().unstack(fill_value=0)
status_counts = status_counts.reindex(index=cordex_domains, columns=status, fill_value=0)
status_counts = status_counts.loc[cordex_domains]
ic(status_counts)
ic(status_counts.sum(axis=1))

status_colors = [colors[s] for s in status]  # Match colors to the order of statuses
status_counts.plot(kind='bar', stacked=True, figsize=(7, 2.5), color=status_colors, zorder=2)
ax = plt.gca()
ax.set_ylim([0, get_ymax(experiment)])
ax.grid(axis='y', linestyle='--', linewidth=0.5, zorder=1)
plt.xlabel('')
plt.xticks(rotation=0)
plt.ylabel('Total number of simulations')
plt.title(f'Simulations by CORDEX domain ({experiment.upper()})')
plt.legend(title='Status', loc='upper center')
plt.tight_layout()
plt.savefig(f'docs/CORDEX_{mip_era}_global_progress__{experiment.upper()}.svg', bbox_inches='tight')
