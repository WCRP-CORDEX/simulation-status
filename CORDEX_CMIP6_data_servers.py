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

from funs import csv2datatable, assign_node_to_sim

def generate_non_esgf_table(servers):
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
    This page collects information about servers hosting CORDEX-CMIP6 data not on ESGF.
    This is an interim solution while ESGF-NG publication is technically possible.
    To add a new server or update existing information, please open an issue or pull request at <a href="https://github.com/WCRP-CORDEX/simulation-status">the GitHub repository</a>.
    The planned ESGF data nodes that should host CORDEX-CMIP6 data are listed on the <a href="CORDEX_CMIP6_esgf_nodes.html">ESGF Nodes</a> page.
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


def generate_esgf_table(servers):
    sims = pd.read_csv('CMIP6_downscaling_plans.csv')
    sims = assign_node_to_sim(sims, servers)

    nodes = pd.DataFrame(servers).drop(columns=['simulations'])

    hosted = sims[sims.node_index != -1]
    nodes['sim_pub'] = hosted[hosted.status == 'published'].groupby('node_index').domain_id.count()
    nodes['sim_tot'] = hosted.groupby('node_index').domain_id.count()
    nodes['sim_pub'] = nodes['sim_pub'].fillna(0)
    nodes['sim_tot'] = nodes['sim_tot'].fillna(0)
    nodes['sim_count'] = nodes.apply(lambda row: f"{row.sim_pub:.0f} ({row.sim_tot:.0f} planned)", axis=1)

    nodes = nodes.drop(columns=['sim_tot', 'sim_pub'])
    nodes = nodes[['name', 'status', 'comment', 'index', 'accepting_requests', 'volume', 'sim_count', 'url']]

    # CSV with non-published simulations, for power users only.
    orphans = sims[sims.node_index == -1].drop(columns=['node_name', 'node_url', 'node_index'])
    orphans.to_csv('docs/CORDEX_CMIP6_orphan_simulations.csv', index=False)
    # Create temporary CSV for processing and ensure cleanup
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp_file:
        csv_file = tmp_file.name
        nodes.to_csv(csv_file, index=False)

    try:
        htmlout = 'docs/CORDEX_CMIP6_esgf_nodes.html'
        title = 'CORDEX-CMIP6 ESGF Data Nodes'
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
    This page collects information about servers hosting ESGF-NG data nodes with CORDEX-CMIP6 data.
    To add a new server or update existing information, please open an issue or pull request at <a href="https://github.com/WCRP-CORDEX/simulation-status">the GitHub repository</a>.
    A raw list of simulations without ESGF node plans is available here: <a href="CORDEX_CMIP6_orphan_simulations.csv">CORDEX_CMIP6_orphan_simulations.csv</a>.
    Some data is already published on servers outside the ESGF ecosystem, as listed on the <a href="CORDEX_CMIP6_data_servers.html">Data Servers</a> page.
    </p>
    '''

        rename_fields = {
            'name' : 'Name',
            'status': 'Status',
            'comment': 'Description',
            'index': 'ESGF Index',
            'accepting_requests': 'Accepting hosting requests',
            'volume' : 'Estimated storage space [TiB]',
            'sim_count': 'Count of simulation hosted',
            'url': 'URL'
        }

        csv2datatable(
            csv_file, 
            htmlout, 
            title=title, 
            intro=intro, 
            rename_fields=rename_fields,
            column_as_link='url',
        )

        print(f"Generated {htmlout} from Yaml file.")
    finally:
        # Clean up temporary CSV
        if os.path.exists(csv_file):
            os.remove(csv_file)




if __name__ == '__main__':
    yaml_file = 'CORDEX_CMIP6_data_servers.yaml'
    with open(yaml_file, 'r') as f:
        servers = yaml.safe_load(f)

    # nonesgf
    generate_non_esgf_table(servers['non-esgf'])

    # ESGF nodes
    generate_esgf_table(servers['esgf'])
