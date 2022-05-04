#!/usr/bin/env python3
import datetime
from pyesgf.search import SearchConnection
import logging
import natsort as ns
import numpy as np
import pandas as pd
import re

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
df = pd.DataFrame()
for proj,dom in [('CORDEX','EUR-11'), ('CORDEX','EUR-44'), ('CORDEX-Reklies','EUR-11')]:
  logger.info(f'Retrieving {proj} variables ...')
  ctx = conn.new_context(project = proj, domain=dom)
  dids = [result.dataset_id for result in ctx.search(batch_size=1000, ignore_facet_check=True)]
  datanode_part = re.compile('\|.*$')
  dataset_ids = [datanode_part.sub('', did).split('.') for did in dids]
  df = df.append(pd.DataFrame(dataset_ids))

df.columns = facets
# Drop unnecessary columns
df.drop(
  ['project', 'activity', 'variable', 'version', 'frequency'],
  axis = 'columns', inplace = True
)
df.drop_duplicates(inplace = True)
df.drop(df[df.ensemble == 'r0i0p0'].index, axis=0, inplace=True)
df.drop(df[df.model.isin(['STARS3','WETTREG2013'])].index, axis=0, inplace=True)
df.sort_values(['domain', 'institution', 'model', 'model_version', 'driving_model', 'ensemble', 'experiment'])

collapse_institutions = True

domains = sorted(list(set(df.domain)))
df = df.assign(status='published') # These are only ESGF published data
df['model'].replace({'REMO2009': 'REMO', 'REMO2015': 'REMO'}, inplace=True)

f = open(f'CMIP5_matrix.html','w')
f.write(f'''<!DOCTYPE html>
<html><head>
<style>
body {{ padding-bottom: 600px; }}
tr:hover {{background-color:#f5f5f5;}}
th, td {{text-align: center; padding: 3px;}}
table {{border-collapse: collapse;}}
span.planned {{color: #FF9999}}
span.running {{color: #009900}}
span.completed {{color: black; font-weight: bold}}
span.published {{color: #3399FF; font-weight: bold}}
a {{color: DodgerBlue}}
a:link {{ text-decoration: none; }}
a:visited {{ text-decoration: none; }}
a:hover {{ text-decoration: underline; }}
a:active {{ text-decoration: underline;}}
</style>
</head><body>
<h1> CORDEX-CMIP5 ESGF summary tables</h1>
<p style="text-align: right;">(Version: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M")})</p>
<p style="text-align: justify;">
Currently only from EURO-CORDEX
<p style="text-align:left"> Domains: |
''')
[f.write(f'<a href="#{dom}">{dom}</a> | ') for dom in domains]
d1 = dict(selector=".level0", props=[('min-width', '100px')])
for domain in domains:
  f.write(f'''<h2 id="{domain}">{domain}</h2>''')
  for exp in ['rcp26', 'rcp45', 'rcp85']:
    dom_df = df[(df.domain == domain) & (df.experiment == exp)]
    dom_df = dom_df.assign(htmlstatus=pd.Series('<span class="' + dom_df.status + '">' + dom_df.experiment + '</span>', index=dom_df.index))
    dom_df = dom_df.assign(instmodel=pd.Series(dom_df.institution + '-' + dom_df.model, index=dom_df.index))
    column_id = 'model' if collapse_institutions else 'instmodel'
    dom_df_matrix = dom_df.pivot_table(
      index = ('driving_model', 'ensemble'),
      columns = column_id,
      values = 'htmlstatus',
      aggfunc = lambda x: ' '.join(x.dropna())
    )
    # Drop evaluation runs and r0 members (coming from static variables)
    dom_df_matrix.drop('ECMWF-ERAINT', level=0, axis=0, inplace=True, errors='ignore')
    f.write(f'''<h3>{exp}</h3>
      <p style="font-size: smaller;"> Colour legend:
        <span class="planned">planned</span>
        <span class="running">running</span>
        <span class="completed">completed</span>
        <span class="published">published</span>
      </p>
    ''')
    f.write(dom_df_matrix.style
       .set_properties(**{'font-size':'8pt', 'border':'1px lightgrey solid !important'})
       .set_table_styles([d1,{
          'selector': 'th',
          'props': [('font-size', '8pt'),('border-style','solid'),('border-width','1px')]
        }])
       .render()
       .replace('nan','')
       .replace('historical','hist')
    )
f.write('</body></html>')
f.close()
