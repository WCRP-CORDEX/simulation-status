#!/usr/bin/env python3
import datetime
import logging
import pandas as pd
import re

from funs import *
from pyesgf.search import SearchConnection

loglevel = logging.INFO
logger = logging.getLogger('root')
logger.setLevel(loglevel)
loghandler = logging.StreamHandler()
loghandler.setFormatter(logging.Formatter('[%(asctime)s] %(message)s'))
logger.addHandler(loghandler)

facets = (
  'project', 'activity', 'domain', 'institution', 'driving_model', 'experiment', 'ensemble',
  'model', 'model_version', 'frequency', 'variable', 'version'
)

#
#   Load search results
#
conn = SearchConnection('http://esgf-data.dkrz.de/esg-search', distrib=True)
logging.getLogger('pyesgf.search.connection').setLevel(loglevel)
dflist = []
for proj in ['CORDEX-FPSCONV']:
  logger.info(f'Retrieving {proj} variables ...')
  ctx = conn.new_context(project = proj)
  dids = [result.dataset_id for result in ctx.search(batch_size=1000, ignore_facet_check=True)]
  datanode_part = re.compile('\|.*$')
  dataset_ids = [datanode_part.sub('', did).split('.') for did in dids]
  dflist.append(pd.DataFrame(dataset_ids))
df = pd.concat(dflist)
df.columns = facets
df.drop(columns = ['frequency', 'variable'], inplace = True)
df.query('ensemble != "r0i0p0"', inplace = True)
df.drop_duplicates(inplace = True)

# Add ESGF search URL
search_urls = []
for idx, row in df.iterrows():
  row_dict = row.to_dict()
  search_urls.append(
    'https://esgf-metagrid.cloud.dkrz.de/search?project=CORDEX&'
      + 'activeFacets=%7B%22project%22%3A%22CORDEX-FPSCONV%22%2C%22experiment%22%3A%22{experiment}%22%2C%22driving_model%22%3A%22{driving_model}%22%2C%22institute%22%3A%22{institution}%22%2C%22domain%22%3A%22{domain}%22%2C%22ensemble%22%3A%22{ensemble}%22%2C%22rcm_name%22%3A%22{model}%22%2C%22rcm_version%22%3A%22{model_version}%22%7D'.format_map(row_dict)
  )
df['search_url'] = search_urls

# Drop unnecessary columns
df.drop(columns = ['project', 'activity', 'version'], inplace = True)
df.drop_duplicates(inplace = True)
# Reorder columns in custom order and sort
df = df[['domain', 'model', 'experiment', 'driving_model', 'ensemble', 'model_version', 'institution', 'search_url']]
df.sort_values(['domain', 'model', 'experiment', 'driving_model', 'ensemble'], key=lambda x: x.str.lower(), inplace = True)

#
#  Simulation and variable list as interactive datatable
#
collapse_institutions = True
domains = sorted(list(set(df.domain)))
df = df.assign(status='published') # These are only ESGF published data
df.to_csv('docs/CORDEX_FPSCONV_ESGF_simulations.csv', index = False)
csv2datatable(
  'docs/CORDEX_FPSCONV_ESGF_simulations.csv',
  'docs/CORDEX_FPSCONV_ESGF_simulations.html',
  column_as_link = 'status',
  column_as_link_source = 'search_url',
  title = 'CORDEX-FPSCONV simulations on ESGF',
  intro = f'''
<p> CORDEX-FPSCONV simulations providing some data on ESGF as of <b>{datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")}</b>. The full list of variables can be obtained from <a href="https://wcrp-cordex.github.io/simulation-status/CORDEX_FPSCONV_varlist.html">here</a>.
'''
)
