import pandas as pd
import matplotlib.pyplot as plt
import sys
from icecream import ic

experiment = sys.argv[1]
mip_era = sys.argv[2]
# Set domain_set to 'all' or 'core' to enable CORE-only filtering
domain_set = sys.argv[3] if len(sys.argv) > 3 else 'all'

if mip_era == 'CMIP5':
  url = "https://raw.githubusercontent.com/WCRP-CORDEX/simulation-status/main/docs/CORDEX_CMIP5_status.csv"
else:
  url = 'https://raw.githubusercontent.com/WCRP-CORDEX/simulation-status/main/CMIP6_downscaling_plans.csv'
  url = 'CMIP6_downscaling_plans.csv'

cordex_domains = ['SAM', 'CAM', 'NAM', 'EUR', 'MED', 'MENA', 'AFR', 'WAS', 'CAS', 'EAS', 'SEA', 'AUS', 'ANT', 'ARC']
# Domains to skip (non CORE)
skip_domains_core = ['ANT', 'ARC', 'MED', 'MNA', 'MENA', 'CAS']
skip_domains = skip_domains_core if domain_set == 'core' else []
cordex_domains = [d for d in cordex_domains if d not in skip_domains]
colors = {
    'published': '#3399FF',
    'completed': '#000000',
    'running': '#009900',
    'planned': '#FF9999'
}
status = colors.keys()

def get_ymax(exp):
  if exp.startswith('ssp'):
    return(125 if domain_set == 'all' else 9)
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
  & ~df['comments'].str.contains('#ESD', na=False)
].query('status in @status')

if domain_set == 'core':
    filtered_df = filtered_df[
        ~filtered_df['domain'].isin(skip_domains)
      & filtered_df['comments'].str.contains('#CORDEX-CORE', na=False)
    ]

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
title = f'CORDEX-CORE {mip_era} simulations ({experiment.upper()})' if domain_set == 'core' else f'Simulations by CORDEX domain ({experiment.upper()})'
plt.title(title)
if domain_set == 'core':
    plt.legend(title='Status', loc='upper left', bbox_to_anchor=(1, 1))
else:
    plt.legend(title='Status', loc='upper center')
plt.tight_layout()
suffix = '__core' if domain_set == 'core' else ''
plt.savefig(f'docs/CORDEX_{mip_era}_global_progress__{experiment.upper()}{suffix}.svg', bbox_inches='tight')
