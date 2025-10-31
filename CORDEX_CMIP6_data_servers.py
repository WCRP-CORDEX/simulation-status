#!/usr/bin/env python
"""
Generate HTML table from CORDEX-CMIP6 data servers YAML file.
This script reads the YAML file and creates an interactive HTML table
using DataTables for filtering and sorting.
"""

import os
import tempfile

import pandas as pd
import yaml

from funs import csv2datatable

# Read YAML file
yaml_file = 'CORDEX_CMIP6_data_servers.yaml'
with open(yaml_file, 'r') as f:
    data = yaml.safe_load(f)

# Convert to DataFrame
servers = data.get('servers', [])
if not servers:
    print(f"Warning: No servers found in {yaml_file}")
    servers = []

df = pd.DataFrame(servers)

# Create temporary CSV for processing and ensure cleanup
with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp_file:
    csv_file = tmp_file.name
    df.to_csv(csv_file, index=False)

try:
    # Generate HTML output
    htmlout = 'docs/CORDEX_CMIP6_data_servers.html'
    title = 'CORDEX-CMIP6 Data Servers'
    intro = '''
<div style="display:table;width:100%;">
  <div style="display:table-row;">
    <div style="display:table-cell;width:50%;">
      <a href="https://wcrp-cordex.github.io/simulation-status">Back to main</a>
    </div>
    <div style="display:table-cell;text-align:right;width:50%;">
      Source: <a href="https://github.com/WCRP-CORDEX/simulation-status/blob/main/CORDEX_CMIP6_data_servers.yaml">CORDEX_CMIP6_data_servers.yaml</a>
    </div>
  </div>
</div>
<p style="text-align: justify;">
This page collects information about servers hosting CORDEX-CMIP6 data, 
including those not (yet) on ESGF. This is an interim solution while ESGF-NG 
publication becomes a reality. To add a new server or update existing information, 
please open an issue or pull request at 
<a href="https://github.com/WCRP-CORDEX/simulation-status">the GitHub repository</a>.
</p>
'''

    rename_fields = {
        'domain': 'Domain',
        'institution': 'Institution',
        'url': 'URL',
        'availability': 'Availability',
        'comment': 'Comment'
    }

    csv2datatable(
        csv_file, 
        htmlout, 
        title=title, 
        intro=intro, 
        rename_fields=rename_fields,
        column_as_link='url'
    )

    print(f"Generated {htmlout} from {yaml_file}")
finally:
    # Clean up temporary CSV
    if os.path.exists(csv_file):
        os.remove(csv_file)
