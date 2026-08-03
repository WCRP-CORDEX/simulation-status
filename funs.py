import datetime
import os
import pandas as pd
import requests
import time
from functools import reduce
from operator import and_, or_
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse


span_style = '''
span.planned {color: #F54d4d; font-weight: bold}
span.running {color: #009900; font-weight: bold}
span.completed {color: #17202a; font-weight: bold}
span.published {color: #3399FF; font-weight: bold}
span.cordex-core {text-decoration: underline; text-underline-offset: 0.15em;}

span.unmigrated {color: #ca6f1e; font-weight: bold}

span.reginst {color: black; font-weight: bold}
span.unreginst {color: grey; font-style: italic; font-weight: bold}
span.unregistered {color: grey; font-style: italic; font-weight: bold}
span.ARCM {color: black; font-weight: bold}
span.AORCM {color: #2980b9; font-weight: bold}
span.AGCM {color: black; font-weight: bold}
span.AOGCM {color: #2980b9; font-weight: bold}
span.ESD {color: #ca6f1e; font-weight: bold}
'''

html_style = '''
<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700&display=swap" rel="stylesheet">
<style>
body {
  font-family: 'Montserrat', sans-serif;
  padding-top: 15px;
  padding-left: 15px;
  padding-right: 15px;
  padding-bottom: 600px;
}
tr:hover {background-color:#f5f5f5;}
th, td {text-align: center; padding: 3px;}
table {border-collapse: collapse;}''' + span_style + '''
a {color: DodgerBlue}
a:link { text-decoration: none; }
a:visited { text-decoration: none; }
a:hover { text-decoration: underline; }
a:active { text-decoration: underline;}
ul.twocol { columns: 2; -webkit-columns: 2; -moz-columns: 2; }
.logo {
  text-align: center;
  margin-bottom: 20px;
}
</style>
'''

html_legend = '''
      <p style="font-size: smaller;"> Colour legend for status:
        (
        <span class="planned">planned</span>
        <span class="running">running</span>
        <span class="completed">completed</span>
        <span class="published">published</span>
        )
        //
        source_type:
        (
        <span class="unregistered">unregistered</span>
        <span class="ARCM">ARCM</span>
        <span class="AORCM">AORCM</span>
        <span class="ESD">ESD</span>
        )
      </p>
'''

table_props = [('width', '100px')]


CMIP6_SIMULATION_KEYS = [
  'domain_id',
  'institution_id',
  'source_id',
  'driving_source_id',
  'driving_variant_label',
  'driving_experiment_id',
]

def html_header(title = 'CORDEX-CMIP6 downscaling plans', mip_era='CMIP6'):
  return(f'''<!DOCTYPE html>
<html><head>
{html_style}
</head><body>
<div class="logo">
<img src="https://cordex.org/wp-content/uploads/2025/02/CORDEX_RGB_logo_baseline_positive-300x133.png" 
   alt="CORDEX Logo" >
<h1 id="top">{title}</h1>
</div>
<div style="display:table;width:100%;">
  <div style="display:table-row;">
    <div style="display:table-cell;width:50%;">
      <a href="https://wcrp-cordex.github.io/simulation-status">Back to main</a>, see
      <a href="./{mip_era}_downscaling_plans.html">full list</a>, or see tables by 
      <a href="./CORDEX_{mip_era}_status.html">domain</a>,
      <a href="./CORDEX_{mip_era}_status_by_scenario.html">scenario</a> or
      <a href="./CORDEX_{mip_era}_status_by_experiment.html">experiment</a>
    </div>
    <div style="display:table-cell;text-align:right;width:50%;">
      (Version: {datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M")} UTC)
    </div>
  </div>
</div>
<p style="text-align: justify;">
Simulation status according to CORDEX-{mip_era} downscaling plans reported by the groups and collected in <a href="https://github.com/WCRP-CORDEX/simulation-status/blob/main/{mip_era}_downscaling_plans.csv">{mip_era}_downscaling_plans.csv</a>. 
To contribute/update simulations open an issue or pull request at <a href="https://github.com/WCRP-CORDEX/simulation-status">https://github.com/WCRP-CORDEX/simulation-status</a>.
'''
  )

def html_footer():
  return('</body></html>')

def addtag(word, field):
  rval = word
  if (field == 'comments') and word.startswith('#'):
    rval = f'<span class="tag">{word[1:]}</span>'
  elif (field == 'comments') and word.startswith('http'):
    rval = f'<a href="{word}">{word}</a>'
  elif (field == 'status') and word in ['selected', 'planned', 'running', 'completed', 'unmigrated', 'published']:
    rval = f'<span class="{word}">{word}</span>'
  return(rval)

def taggify(text, field):
  rval = text
  if field in ['status', 'comments']:
    rval = ' '.join([addtag(x, field) for x in text.split(' ')])
  elif isinstance(rval, bool):
    rval = '&#x2705;' if rval else '&#x274C;'
  return(rval)

def csv2datatable(csvfile, htmlout, title='', intro='', rename_fields = {}, column_as_link="", column_as_link_source=""):
  plans = pd.read_csv(csvfile, na_filter=False)
  if column_as_link:
    if not column_as_link_source:
      column_as_link_source = column_as_link
    plans[column_as_link] = (
      '<a href="' + plans[column_as_link_source] + '">' + plans[column_as_link] + "</a>"
    )
  if column_as_link != column_as_link_source:
    plans.drop(columns=column_as_link_source, inplace=True)

  field_names = dict(zip(plans.columns,plans.columns))
  field_names.update(rename_fields)
  fp = open(htmlout,'w')
  fp.write('''<!DOCTYPE html>
<html lang="en">
<head>
<meta name="author" content="J. Fernandez" />
<meta name="keywords" content="HTML, CSS, JavaScript" />
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700&display=swap" rel="stylesheet">
<link rel="stylesheet" type="text/css" href="https://cdn.datatables.net/1.11.5/css/jquery.dataTables.css">
<script type="text/javascript" charset="utf8" src="https://code.jquery.com/jquery-3.5.1.js"></script>
<script type="text/javascript" charset="utf8" src="https://cdn.datatables.net/1.11.5/js/jquery.dataTables.js"></script>

''')
  if title:
    fp.write(f'<title>{title}</title>')
  fp.write(f'''
<style>
body {{
  font-family: "Montserrat", sans-serif;
  padding-top: 15px;
  padding-left: 15px;
  padding-right: 15px;
  padding-bottom: 600px;
}}
span.tag {{
  background-color: #c5def5;
  padding: 0 10px;
  font-size: 12px;
  font-weight: 500;
  line-height: 22px !important;
  border: 1px solid transparent;
  border-radius: 2em;
}}
a {{color: DodgerBlue}}
a:link {{ text-decoration: none; }}
a:visited {{ text-decoration: none; }}
a:hover {{ text-decoration: underline; }}
a:active {{ text-decoration: underline;}}
{span_style}
.logo {{
  text-align: center;
  margin-bottom: 20px;
}}
</style>
</head>
<body>
''')
  if title:
    fp.write(f'''
<div class="logo">
<img src="https://cordex.org/wp-content/uploads/2025/02/CORDEX_RGB_logo_baseline_positive-300x133.png" 
   alt="CORDEX Logo" >
<h1 id="top">{title}</h1>
</div>
''')
  if intro:
    fp.write(f'{intro}')
  fp.write('''
<table id="table_id" class="display">
    <thead>
        <tr>
''')
  [fp.write(f'              <th>{field_names[x]}</th>\n') for x in plans]
  fp.write(f'''
        </tr>
    </thead>
    <tbody>
''')
  for idx, plan in plans.iterrows():
    fp.write(f'        <tr>\n')
    for field,item in zip(plans.columns, plan):
      fp.write(f'            <td>{taggify(item, field)}</td>\n')
    fp.write(f'        </tr>\n')
  fp.write('''
    </tbody>
</table>
    <script>
        // URL parameter helpers - using older browser-compatible methods
        function getParam(name) {
            var urlParams = new URLSearchParams(window.location.search);
            return urlParams.get(name) || '';
        }
        
        function setParam(name, value) {
            var url = new URL(window.location);
            if (value && value !== '') {
                url.searchParams.set(name, value);
            } else {
                url.searchParams.delete(name);
            }
            window.history.replaceState({}, '', url);
        }

        $(document).ready(function() {
            // Get initial values from URL
            var initialSearch = getParam('search');
            var initialLength = parseInt(getParam('length')) || 20;
            var initialOrder = getParam('order');
            
            var initialOrderArray = [[0, 'asc']]; // default
            if (initialOrder) {
                try {
                    initialOrderArray = JSON.parse(initialOrder);
                } catch (e) {
                    console.log('Could not parse order parameter');
                }
            }
            
            // Initialize DataTable with URL parameters
            var table = $('#table_id').DataTable({
                pageLength: initialLength,
                lengthMenu: [20, 50, 100, 200, 500],
                order: initialOrderArray,
                searching: true
            });
            
            // Set initial search if provided
            if (initialSearch) {
                table.search(initialSearch).draw();
            }
            
            // Update URL when search changes
            table.on('search.dt', function() {
                var searchValue = table.search();
                setParam('search', searchValue);
            });
            
            // Update URL when page length changes  
            table.on('length.dt', function(e, settings, len) {
                setParam('length', len == 20 ? '' : len);
            });
            
            // Update URL when column order changes
            table.on('order.dt', function() {
                var currentOrder = table.order();
                setParam('order', JSON.stringify(currentOrder));
            });
            
            console.log('DataTable initialized with URL management');
        });
    </script>
</body>
</html>''')
  fp.close()


def add_registration_info(plans_df, cmip_era='CMIP6'):
  """
  Add registration information from CORDEX CV repositories.
  
  Parameters:
  -----------
  plans_df : pandas.DataFrame
      DataFrame with simulation plans containing 'source_id' and 'institution_id' columns
  cmip_era : str
      Either 'CMIP6' or 'CMIP7' to determine which CV repo to use
      
  Returns:
  --------
  pandas.DataFrame
      Modified DataFrame with added columns: 'registered', 'source_type', 'inst_registered'
  """
  base_url = f"https://raw.githubusercontent.com/WCRP-CORDEX/cordex-{cmip_era.lower()}-cv/refs/heads/main/CORDEX-{cmip_era}"
  
  # Fetch source_id registration info
  url_source_id = f"{base_url}_source_id.json"
  try:
    response = requests.get(url_source_id)
    response.raise_for_status()
    source_ids = response.json()["source_id"]
    source_type_map = {key: value["source_type"] for key, value in source_ids.items()}
    plans_df["registered"] = plans_df["source_id"].apply(lambda x: x in source_type_map)
    plans_df["source_type"] = plans_df["source_id"].apply(
      lambda x: source_type_map.get(x, "") if x in source_type_map else "unregistered"
    )
  except (requests.exceptions.HTTPError, requests.exceptions.RequestException) as e:
    # CV repo doesn't exist yet or is unavailable - mark all as unregistered
    print(f"Warning: Could not fetch source_id CV from {url_source_id}: {e}")
    plans_df["registered"] = False
    plans_df["source_type"] = "unregistered"
  
  # Fetch institution_id registration info
  url_institution_id = f"{base_url}_institution_id.json"
  try:
    response = requests.get(url_institution_id)
    response.raise_for_status()
    institution_ids = response.json()["institution_id"]
    plans_df["inst_registered"] = plans_df["institution_id"].apply(
      lambda x: "reginst" if x in institution_ids else "unreginst"
    )
  except (requests.exceptions.HTTPError, requests.exceptions.RequestException) as e:
    # CV repo doesn't exist yet or is unavailable - mark all as unregistered
    print(f"Warning: Could not fetch institution_id CV from {url_institution_id}: {e}")
    plans_df["inst_registered"] = "unreginst"
  
  return plans_df


def generate_domain_table(dom_plans, collapse_institutions=True):
  """
  Generate a pivot table matrix for a specific domain with HTML styling.
  
  Parameters:
  -----------
  dom_plans : pandas.DataFrame
      DataFrame containing simulation plans for a specific domain
  collapse_institutions : bool
      Whether to collapse institutions in the table display
      
  Returns:
  --------
  pandas.DataFrame
      Styled pivot table ready for HTML export
  """
  is_cordex_core = dom_plans.comments.fillna('').str.contains('#CORDEX-CORE', case=False, na=False)
  # Add HTML status column
  dom_plans = dom_plans.assign(
    htmlstatus=pd.Series(
      '<span sort="' + dom_plans.driving_experiment_id + '" class="' + 
      (dom_plans.status + is_cordex_core.map(lambda flagged: ' cordex-core' if flagged else '')) +
      '">' + dom_plans.driving_experiment_id + '</span>', 
      index=dom_plans.index
    )
  )
  
  # Add HTML-styled source_id and institution_id
  dom_plans = dom_plans.assign(
    source_id=pd.Series(
      '<span sort="' + dom_plans.source_id + '" class="' + 
      dom_plans.source_type + '">' + dom_plans.source_id + '</span>', 
      index=dom_plans.index
    )
  )
  dom_plans = dom_plans.assign(
    institution_id=pd.Series(
      '<span sort="' + dom_plans.institution_id + '" class="' + 
      dom_plans.inst_registered + '">' + dom_plans.institution_id + '</span>', 
      index=dom_plans.index
    )
  )
  dom_plans = dom_plans.assign(
    model_id=pd.Series(
      dom_plans.institution_id + '-' + dom_plans.source_id, 
      index=dom_plans.index
    )
  )
  
  # Create pivot table
  column_id = 'source_id' if collapse_institutions else 'model_id'
  dom_plans_matrix = dom_plans.pivot_table(
    index=('driving_source_id', 'driving_variant_label'),
    columns=column_id,
    values='htmlstatus',
    aggfunc=lambda x: ' '.join(sorted(x.dropna()))
  )
  
  # Bring ERA5 to the top
  dom_plans_matrix = pd.concat([
    dom_plans_matrix.query("driving_source_id == 'ERA5'"),
    dom_plans_matrix.drop(('ERA5', ''), axis=0, errors='ignore')
  ], axis=0)
  
  # Add institution row if collapsing
  if collapse_institutions:
    inst = dom_plans.drop_duplicates(subset=['institution_id', 'source_id']).pivot_table(
      index=('driving_source_id', 'driving_variant_label'),
      columns='source_id',
      values='institution_id',
      aggfunc=lambda x: ', '.join(x.dropna())
    ).agg(lambda x: ', '.join(x.dropna()))
    inst.name = ('', 'Institutes')
    dom_plans_matrix = pd.concat([dom_plans_matrix, inst.to_frame().T])
    dom_plans_matrix = dom_plans_matrix.T.set_index([('', 'Institutes'), dom_plans_matrix.columns]).T
    dom_plans_matrix.columns.names = ['Institution(s)', 'RCM']
  
  return dom_plans_matrix


def assign_node_to_sim(simulations, nodes):
  """Using the ESGF nodes list and adds the node_name, node_url and node_index columns.
  
  node_index is the index into the list of nodes.
  """
  sims = simulations.copy()
  sims['node_url'] = None
  sims['node_name'] = None
  sims['node_index'] = -1

  for i, node in enumerate(nodes):
    if not node.get('simulations'):
      continue

    match = []
    for j, terms in enumerate(node['simulations']):
      this_match = reduce(and_, [sims[k].isin([v] if isinstance(v, str) else v) for k, v in terms.items()])
      if not this_match.any():
        raise ValueError(f'Search term {j} of node {i} does not match any simulation.')
      match.append(this_match)

    hosted = sims[reduce(or_, match)]
    if (dups := set(hosted.index).intersection(set(sims[sims.node_index != -1].index))):
      raise ValueError(f"Node {i} matches {len(dups)} simulations already matched by previous nodes : {sims[list(dups)]}")

    sims.loc[hosted.index, 'node_url'] = node['url']
    sims.loc[hosted.index, 'node_name'] = node['name']
    sims.loc[hosted.index, 'node_index'] = i

  return sims


def _normalize_variant_label(experiment_id, variant_label):
  """Normalize variant labels to match the plans CSV convention."""
  if str(experiment_id).strip().lower() == 'evaluation':
    return ''
  if pd.isna(variant_label):
    return ''
  return str(variant_label).strip()


def _extract_asset_nodes(assets):
  """Extract hosting node names from STAC assets, ignoring globus endpoints."""
  def _clean_node(node_name):
    if not node_name:
      return None
    node_name = str(node_name).strip()
    if not node_name:
      return None
    if 'globus' in node_name.lower():
      return None
    return node_name

  nodes = set()
  for asset in (assets or {}).values():
    if not isinstance(asset, dict):
      continue

    # Prefer alternate:name from STAC metadata when available.
    alt_name = _clean_node(asset.get('alternate:name'))
    if alt_name:
      nodes.add(alt_name)
      continue

    href = asset.get('href', '')
    if href:
      host = urlparse(str(href)).hostname
      host = _clean_node(host)
      if host:
        nodes.add(host)
  return nodes


def _version_to_yyyy_mm(version_value):
  """Convert version format vYYYYMMDD or YYYYMMDD to YYYY-MM."""
  s = str(version_value)
  return f'{s[1:5]}-{s[5:7]}' if s.startswith('v') else f'{s[0:4]}-{s[4:6]}'


def _iter_stac_features(items_url, timeout=60, paginate=True, limit=20000):
  """Yield STAC features with optional rel=next pagination traversal."""
  next_url = _ensure_limit_query(items_url, default_limit=limit)

  if not paginate:
    payload = _get_json_with_retries(next_url, timeout=timeout)
    for feature in payload.get('features', []):
      yield feature

    number_returned = payload.get('numberReturned')
    number_matched = payload.get('numberMatched')
    if number_returned is not None and number_matched is not None and number_returned < number_matched:
      print(
        'Warning: STAC single-request mode returned '
        f'{number_returned}/{number_matched} items. '
        'Enable paginate=True for full traversal.'
      )
    return

  seen_urls = set()
  while next_url:
    if next_url in seen_urls:
      raise RuntimeError(f'Pagination loop detected in STAC response for URL: {next_url}')
    seen_urls.add(next_url)

    payload = _get_json_with_retries(next_url, timeout=timeout)

    for feature in payload.get('features', []):
      yield feature

    next_link = None
    for link in payload.get('links', []):
      if link.get('rel') == 'next':
        next_link = link.get('href')
        break
    next_url = next_link


def _ensure_limit_query(items_url, default_limit=20000):
  """Attach a sensible limit to STAC item queries if not present."""
  parsed = urlparse(items_url)
  query = parse_qs(parsed.query, keep_blank_values=True)
  if 'limit' not in query:
    query['limit'] = [str(default_limit)]
    return urlunparse(parsed._replace(query=urlencode(query, doseq=True)))
  return items_url


def _get_json_with_retries(url, timeout=60, max_attempts=8, backoff_base_seconds=1.5):
  """Fetch JSON with retry/backoff for transient STAC API failures."""
  for attempt in range(1, max_attempts + 1):
    try:
      response = requests.get(url, timeout=timeout)
      response.raise_for_status()
      return response.json()
    except requests.exceptions.RequestException as err:
      status_code = getattr(getattr(err, 'response', None), 'status_code', None)
      retriable = status_code in [429, 500, 502, 503, 504] or status_code is None
      if attempt >= max_attempts or not retriable:
        raise

      wait_s = min(60.0, backoff_base_seconds * (2 ** (attempt - 1)))
      print(
        f'Warning: STAC request failed (attempt {attempt}/{max_attempts}, '
        f'status={status_code}) for {url}. Retrying in {wait_s:.1f}s...'
      )
      time.sleep(wait_s)


def get_cmip6_stac_publication_table(
  items_url='https://api.stac.esgf.ceda.ac.uk/collections/CORDEX-CMIP6/items',
  timeout=60,
  paginate=True,
  limit=20000,
):
  """Build simulation-level publication metadata from CORDEX-CMIP6 STAC items."""
  rows = []
  for feature in _iter_stac_features(
    items_url=items_url,
    timeout=timeout,
    paginate=paginate,
    limit=limit,
  ):
    props = feature.get('properties', {})
    if not props.get('latest', False):
      continue
    if props.get('retracted', False):
      continue

    row = {
      'domain_id': str(props.get('cordex-cmip6:domain_id', '')).strip(),
      'institution_id': str(props.get('cordex-cmip6:institution_id', '')).strip(),
      'source_id': str(props.get('cordex-cmip6:source_id', '')).strip(),
      'driving_source_id': str(props.get('cordex-cmip6:driving_source_id', '')).strip(),
      'driving_experiment_id': str(props.get('cordex-cmip6:driving_experiment_id', '')).strip(),
      'driving_variant_label': _normalize_variant_label(
        props.get('cordex-cmip6:driving_experiment_id', ''),
        props.get('cordex-cmip6:driving_variant_label', ''),
      ),
      'estimated_completion_date': _version_to_yyyy_mm(props.get('version', '')),
      'asset_nodes': _extract_asset_nodes(feature.get('assets')),
      'n_datasets': 1,
    }

    if all(row[k] for k in ['domain_id', 'institution_id', 'source_id', 'driving_source_id', 'driving_experiment_id']):
      rows.append(row)

  if not rows:
    return pd.DataFrame(columns=CMIP6_SIMULATION_KEYS + ['data_node', 'n_datasets'])

  stac = pd.DataFrame(rows)
  grouped = stac.groupby(CMIP6_SIMULATION_KEYS, as_index=False).agg(
    estimated_completion_date=('estimated_completion_date', 'max'),
    asset_nodes=('asset_nodes', lambda values: sorted(set().union(*values))),
    n_datasets=('n_datasets', 'sum'),
  )
  grouped['data_node'] = grouped['asset_nodes'].apply(lambda nodes: ';'.join(nodes))
  grouped.drop(columns=['asset_nodes'], inplace=True)
  return grouped


def apply_cmip6_publication_overlay(plans, publication, report_missing=True):
  """Apply STAC publication metadata to a plans dataframe without any STAC calls."""
  merged = plans.copy()

  plan_key_map = merged.groupby(CMIP6_SIMULATION_KEYS, sort=False).indices
  missing_publications = []

  for _, pub_row in publication.iterrows():
    key = tuple(pub_row[k] for k in CMIP6_SIMULATION_KEYS)
    if key in plan_key_map:
      idx = list(plan_key_map[key])
      merged.loc[idx, 'status'] = 'published'
      if pub_row.get('estimated_completion_date', ''):
        merged.loc[idx, 'estimated_completion_date'] = pub_row['estimated_completion_date']
    else:
      missing_publications.append(pub_row)

  if report_missing:
    print(f'Published simulations found in plans: {len(publication) - len(missing_publications)}')
    print(f'Published simulations missing from plans: {len(missing_publications)}')
    if missing_publications:
      missing_df = pd.DataFrame(missing_publications)
      cols = CMIP6_SIMULATION_KEYS + ['estimated_completion_date', 'n_datasets', 'data_node']
      print('\nPublished simulations missing from plans (first 20):')
      print(missing_df[cols].head(20).to_string(index=False))

  return merged


def load_cmip6_plans_with_publication_overlay(
  plans_csv='CMIP6_downscaling_plans.csv',
  cache_csv='CMIP6_downscaling_plans_merged.csv',
  report_missing=True,
  use_cache=True,
  refresh_cache=False,
):
  """Load the local merged cache; never call STAC from this helper."""
  plans = pd.read_csv(plans_csv, na_filter=False)

  if use_cache and not refresh_cache and os.path.exists(cache_csv):
    cached = pd.read_csv(cache_csv, na_filter=False)
    if list(cached.columns) == list(plans.columns):
      return cached
    print(f'Ignoring outdated cache schema in {cache_csv}; falling back to {plans_csv}.')

  return plans


