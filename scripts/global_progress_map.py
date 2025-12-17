import pandas as pd
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import sys
import glob
from icecream import ic

experiment = sys.argv[1]
mip_era = sys.argv[2]
# Set domain_set to 'all' or 'core' to enable CORE-only filtering
domain_set = sys.argv[3] if len(sys.argv) > 3 else 'all'

if mip_era == 'CMIP5':
    url = "https://raw.githubusercontent.com/WCRP-CORDEX/simulation-status/main/docs/CORDEX_CMIP5_status.csv"
else:
    url = 'https://raw.githubusercontent.com/WCRP-CORDEX/simulation-status/main/CMIP6_downscaling_plans.csv'

cordex_domains = ['SAM', 'CAM', 'NAM', 'EUR', 'MED', 'MENA', 'AFR', 'WAS', 'CAS', 'EAS', 'SEA', 'AUS', 'ANT', 'ARC']
# Domains to skip (non CORE)
skip_domains_core = ['ANT', 'ARC', 'MED', 'MNA', 'MENA', 'CAS']
skip_domains = skip_domains_core if domain_set == 'core' else []
cordex_domains = [d for d in cordex_domains if d not in skip_domains]
cordex_color = "#6E6E6E"  
colors = {
    'published': '#3399FF',
    'completed': '#000000',
    'running': '#009900',
    'planned': '#FF9999'
}
status = colors.keys()

# Font size for map annotations and legend
FONT_SIZE = 14
LINE_HEIGHT_AXES = 0.03
COL_WIDTH_AXES = 0.02

def plot_cordex_boundaries(ax):
    """Plot CORDEX domain boundaries on the map"""
    for border_file in glob.glob('CORDEX_domain_borders/CORDEX_*_border.dat'):
        # Extract domain name and skip if in skip list
        dom = border_file.replace('CORDEX_domain_borders/CORDEX_', '')
        dom = dom.replace('-44_border.dat', '')
        if dom in skip_domains:
            continue
        dborder = pd.read_csv(border_file, sep=' ', header=None)
        ax.plot(*dborder.values.T, '-', color=cordex_color, linewidth=2, 
                transform=ccrs.PlateCarree(), zorder=1)

# Read simulation data
df = pd.read_csv(url)
df[['domain', 'resolution']] = df['domain_id'].str.split('-', expand=True)
if mip_era == 'CMIP5':
    df['comments'] = ''  # Just to make the comments column exist
    df = df[df['resolution'].notna()].query('~resolution.str.endswith("i")')  # avoid double-counting DOM-XXi sims

conditions = [
     ~df['driving_experiment_id'].isna()
    , df['driving_experiment_id'].str.startswith(experiment)
    , ~df['comments'].str.contains('#ESD', na=False)
]

if domain_set == 'core':
    conditions.append(~df['domain'].isin(skip_domains))
    conditions.append(df['comments'].str.contains('#CORDEX-CORE', na=False))

mask = pd.Series(True, index=df.index)
for cond in conditions:
    mask &= cond

filtered_df = df[mask].query('status in @status')

# Count by domain_id (specific resolution)
status_counts_by_domain_id = filtered_df.groupby(['domain_id', 'status']).size().unstack(fill_value=0)
status_counts_by_domain_id = status_counts_by_domain_id.reindex(columns=status, fill_value=0)

# Count by domain (all resolutions combined)
status_counts_by_domain = filtered_df.groupby(['domain', 'status']).size().unstack(fill_value=0)
status_counts_by_domain = status_counts_by_domain.reindex(index=cordex_domains, columns=status, fill_value=0)

# Print tables
print("\n=== Counts by domain_id (specific resolution) ===")
ic(status_counts_by_domain_id)
print("\n=== Counts by domain (all resolutions) ===")
ic(status_counts_by_domain)
print("\n=== Total by domain ===")
ic(status_counts_by_domain.sum(axis=1))

# Manually defined domain centers (axes fractions [0,1])
manual_centers = {
    'SAM': {'x': 0.35, 'y': 0.30},
    'CAM': {'x': 0.33, 'y': 0.55},
    'NAM': {'x': 0.28, 'y': 0.77},
    'EUR': {'x': 0.55, 'y': 0.885},
    'AFR': {'x': 0.58, 'y': 0.40},
    'WAS': {'x': 0.73, 'y': 0.60},
    'EAS': {'x': 0.83, 'y': 0.75},
    'SEA': {'x': 0.85, 'y': 0.50},
    'AUS': {'x': 0.92, 'y': 0.35},
    'ANT': {'x': 0.55, 'y': 0.04},
    'ARC': {'x': 0.55, 'y': 0.965},
    'MED': {'x': 0.56, 'y': 0.72},
    'MENA': {'x': 0.60, 'y': 0.55},
    'CAS': {'x': 0.73, 'y': 0.85}
}

domain_centers = pd.DataFrame(manual_centers).T
domain_centers = domain_centers.loc[cordex_domains, ['x', 'y']]

print("\n=== Domain centers (axes fractions [0,1]) ===")
ic(domain_centers)

# Merge counts with domain centers
status_counts_by_domain['total'] = status_counts_by_domain.sum(axis=1)
map_data = status_counts_by_domain.join(domain_centers, how='inner')

print("\n=== Map data ===")
ic(map_data)

# Map
fig = plt.figure(figsize=(16, 10))
ax = plt.axes(projection=ccrs.Robinson())
ax.add_feature(cfeature.LAND, facecolor="#ADF0D8")
ax.set_global()
plot_cordex_boundaries(ax)

for domain, row in map_data.iterrows():
    # Axes-fraction placement
    base_x, base_y = float(row['x']), float(row['y'])
    T = ax.transAxes
    lh = LINE_HEIGHT_AXES
    cw = COL_WIDTH_AXES
    domain_ids = status_counts_by_domain_id[status_counts_by_domain_id.index.str.startswith(f'{domain}-')]
    table_data = []
    for domain_id in domain_ids.index:
        counts = domain_ids.loc[domain_id]
        table_data.append([domain_id] + [int(counts[s]) for s in status])
    
    # Add total line for domain
    total_counts = row[list(status)]
    table_data.append([domain] + [int(total_counts[s]) for s in status])
    
    num_rows = len(table_data)
    
    # Starting position (slightly above center to account for multiple rows)
    start_y = base_y + (num_rows - 1) * lh / 2
    
    for i, row_data in enumerate(table_data):
        label = row_data[0]
        counts = row_data[1:]
        is_bold = (i == num_rows - 1)  # Last row is bold (domain total)
        
        current_y = start_y - i * lh
        
        # Draw label (left-aligned)
        ax.text(base_x - cw * 2, current_y, f'{label}:',
            ha='right', va='center', fontsize=FONT_SIZE,
            fontweight='bold' if is_bold else 'normal',
            transform=T,
            bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.8, edgecolor='none'))
    
        # Draw each count in its own column with color
        for j, (stat, count) in enumerate(zip(status, counts)):
            ax.text(base_x - cw * 1.5 + j * cw, current_y, str(count),
                ha='center', va='center', fontsize=FONT_SIZE,
                fontweight='bold' if is_bold else 'normal',
                color=colors[stat],
                transform=T,
                bbox=dict(boxstyle='round,pad=0.15', facecolor='white', alpha=0.7, edgecolor='none'))

# Create legend
legend_elements = [plt.Rectangle((0, 0), 1, 1, fc=colors[s], label=s.capitalize()) 
                   for s in status]
ax.legend(handles=legend_elements, loc='lower left', title='Status', framealpha=0.9,
          prop={'size': 11}, title_fontsize=11)

core_tag = ' CORDEX-CORE only' if domain_set == 'core' else ''
plt.title(f'CORDEX-{mip_era} simulations by domain ({experiment.upper()}){core_tag}', fontsize=14, fontweight='bold')
plt.tight_layout()

suffix = '__core' if domain_set == 'core' else ''
# plt.savefig(f'docs/CORDEX_{mip_era}_global_progress_map__{experiment.UPPER()}{suffix}.png',
#             dpi=300, bbox_inches='tight')
plt.savefig(f'docs/CORDEX_{mip_era}_global_progress_map__{experiment.upper()}{suffix}.svg',
            bbox_inches='tight')
print(f"\nMap saved to docs/CORDEX_{mip_era}_global_progress_map__{experiment.upper()}{suffix}.png/svg")