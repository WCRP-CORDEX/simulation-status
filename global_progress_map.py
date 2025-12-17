import pandas as pd
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import sys
import glob
from icecream import ic

experiment = 'ssp'# sys.argv[1]
mip_era = 'CMIP6' # sys.argv[2]
core_only = False

if mip_era == 'CMIP5':
    url = "https://raw.githubusercontent.com/WCRP-CORDEX/simulation-status/main/docs/CORDEX_CMIP5_status.csv"
else:
    url = 'https://raw.githubusercontent.com/WCRP-CORDEX/simulation-status/main/CMIP6_downscaling_plans.csv'

cordex_domains = ['SAM', 'CAM', 'NAM', 'EUR', 'MED', 'MENA', 'AFR', 'WAS', 'CAS', 'EAS', 'SEA', 'AUS', 'ANT', 'ARC']
# Domains to skip (non CORE)
skip_domains_core = ['ANT', 'ARC', 'MED', 'MNA', 'MENA', 'CAS']
skip_domains = skip_domains_core if core_only else []
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
line_height = 4.5  # Degrees latitude spacing between lines
col_width = 8    # Degrees longitude spacing between columns

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

if core_only:
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

# Compute domain centers from border files (automatic)
domain_centers_auto = []
for border_file in glob.glob('CORDEX_domain_borders/CORDEX_*_border.dat'):
    dom = border_file.replace('CORDEX_domain_borders/CORDEX_', '')
    dom = dom.replace('-44_border.dat', '')
    if dom in skip_domains:  # Skip domains in skip list
        continue
    dborder = pd.read_csv(border_file, sep=' ', header=None)
    dclon, dclat = dborder.median().values
    domain_centers_auto.append(dict(domain=dom, lon=dclon, lat=dclat))
domain_centers_auto = pd.DataFrame(domain_centers_auto)
domain_centers_auto = domain_centers_auto.set_index('domain')

# Manual domain centers (you can adjust these coordinates)
manual_centers = {
    'SAM': {'lon': -40.569137, 'lat': -45},
    'CAM': {'lon': -97.705204, 'lat': 6.068755},
    'NAM': {'lon': -96.992134, 'lat': 45},
    'EUR': {'lon': 9.999146, 'lat': 64.574274},
    'AFR': {'lon': 17.820000, 'lat': -41},
    'WAS': {'lon': 80.996487, 'lat': -5.074282},
    'EAS': {'lon': 164.340718, 'lat': 45.838358},
    'SEA': {'lon': 138.080002, 'lat': 20.580000},
    'AUS': {'lon': 120.152981, 'lat': -41},
}
manual_centers = {
    'SAM': {'lon': -50.569137, 'lat': -25},
    'CAM': {'lon': -65.705204, 'lat': 10.068755},
    'NAM': {'lon': -96.992134, 'lat': 45},
    'EUR': {'lon': 15.999146, 'lat': 50.574274},
    'AFR': {'lon': 25.820000, 'lat': -2},
    'WAS': {'lon': 80.996487, 'lat': 14.074282},
    'EAS': {'lon': 125.340718, 'lat': 35.838358},
    'SEA': {'lon': 130.080002, 'lat': 7.580000},
    'AUS': {'lon': 150.152981, 'lat': -25},
    'ANT': {'lon': -10.0, 'lat': -75.0},
    'ARC': {'lon': 0.0, 'lat': 75.0},
    'MED': {'lon': 25.0, 'lat': 40.0},
    'MENA': {'lon': 30.0, 'lat': 20.0},
    'CAS': {'lon': 80.0, 'lat': 50.0}
}

domain_centers = pd.DataFrame(manual_centers).T.loc[cordex_domains, :]

print("\n=== Domain centers (automatic) ===")
ic(domain_centers_auto)
print("\n=== Domain centers (manual - you can edit these) ===")
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
    lon, lat = row['lon'], row['lat']
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
    start_lat = lat + (num_rows - 1) * line_height / 2
    
    for i, row_data in enumerate(table_data):
        label = row_data[0]
        counts = row_data[1:]
        is_bold = (i == num_rows - 1)  # Last row is bold (domain total)
        
        current_lat = start_lat - i * line_height
        
        # Draw label (left-aligned)
        ax.text(lon - col_width * 2, current_lat, f'{label}:',
            ha='right', va='center', fontsize=FONT_SIZE,
            fontweight='bold' if is_bold else 'normal',
            transform=ccrs.PlateCarree(),
            bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.8, edgecolor='none'))
    
        # Draw each count in its own column with color
        for j, (stat, count) in enumerate(zip(status, counts)):
            ax.text(lon - col_width * 1.5 + j * col_width, current_lat, str(count),
                ha='center', va='center', fontsize=FONT_SIZE,
                fontweight='bold' if is_bold else 'normal',
                color=colors[stat],
                transform=ccrs.PlateCarree(),
                bbox=dict(boxstyle='round,pad=0.15', facecolor='white', alpha=0.7, edgecolor='none'))

# Create legend
legend_elements = [plt.Rectangle((0, 0), 1, 1, fc=colors[s], label=s.capitalize()) 
                   for s in status]
ax.legend(handles=legend_elements, loc='lower left', title='Status', framealpha=0.9,
          prop={'size': 11}, title_fontsize=11)

plt.title(f'CORDEX-{mip_era} simulations by domain ({experiment.upper()})', fontsize=14, fontweight='bold')
plt.tight_layout()
#plt.savefig(f'docs/CORDEX_{mip_era}_global_progress_map__{experiment.upper()}.png', 
#            dpi=300, bbox_inches='tight')
plt.savefig(f'docs/CORDEX_{mip_era}_global_progress_map__{experiment.upper()}.svg', 
            bbox_inches='tight')
print(f"\nMap saved to docs/CORDEX_{mip_era}_global_progress_map__{experiment.upper()}.png/svg")