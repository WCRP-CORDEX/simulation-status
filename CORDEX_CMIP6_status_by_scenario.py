#!/usr/bin/env python3
import datetime
import natsort as ns
import numpy as np
import pandas as pd
import re
from funs import html_style
from pyesgf.search import SearchConnection

df = pd.read_csv('CMIP6_downscaling_plans.csv')

# Drop unnecessary columns
df.drop(
  ['contact', 'estimated_completion_date', 'comments'],
  axis = 'columns', inplace = True
)
df.drop_duplicates(inplace = True)

collapse_institutions = True

domains = sorted(list(set(df.domain)))

f = open(f'docs/CORDEX_CMIP6_status_by_scenario.html','w')
f.write(f'''<!DOCTYPE html>
<html><head>
{html_style}
</head><body>
<h1> CORDEX-CMIP6 downscaling plans summary tables (split by SSP)</h1>
<p style="text-align: right;">(Version: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M")})</p>
<p style="text-align: justify;">
Simulation status according to CORDEX-CMIP6 downscaling plans reported by the groups and collected in <a href="https://github.com/WCRP-CORDEX/simulation-status/blob/main/CMIP6_downscaling_plans.csv">CMIP6_downscaling_plans.csv</a>. Check that file for further details.
To contribute/update simulations use this <a href="https://docs.google.com/document/d/1Jy53yvB9SDOiWcwKRJc_HpWVgmjxZhy-qVviHl6ymDM/edit?usp=sharing">Google doc</a>.
<p style="text-align: justify;">
See also the SSP-collapsed tables <a href="https://wcrp-cordex.github.io/simulation-status/CORDEX_CMIP6_status.html">here</a>.
<p style="text-align:left"> Domains: |
''')
[f.write(f'<a href="#{dom}">{dom}</a> | ') for dom in domains]
d1 = dict(selector=".level0", props=[('min-width', '100px')])
for domain in domains:
  f.write(f'''<h2 id="{domain}">{domain}</h2>''')
  for exp in ['ssp119', 'ssp126', 'ssp245', 'ssp370', 'ssp585']:
    dom_df = df[(df.domain == domain) & (df.experiment == exp)]
    dom_df = dom_df.assign(htmlstatus=pd.Series('<span class="' + dom_df.status + '">' + dom_df.experiment + '</span>', index=dom_df.index))
    dom_df = dom_df.assign(instmodel=pd.Series(dom_df.institute + '-' + dom_df.rcm_name, index=dom_df.index))
    column_id = 'rcm_name' if collapse_institutions else 'instmodel'
    dom_plans_matrix = dom_df.pivot_table(
      index = ('driving_model', 'ensemble'),
      columns = column_id,
      values = 'htmlstatus',
      aggfunc = lambda x: ' '.join(x.dropna())
    )
    if collapse_institutions:
      inst = dom_df.drop_duplicates(subset=['institute','rcm_name']).pivot_table(
        index = ('driving_model', 'ensemble'),
        columns = 'rcm_name',
        values = 'institute',
        aggfunc = lambda x: ', '.join(x.dropna())
      ).agg(lambda x: ', '.join(x.dropna()))
      inst.name = ('','Institutes')
      dom_plans_matrix = pd.concat([dom_plans_matrix, inst.to_frame().T])
      dom_plans_matrix = dom_plans_matrix.T.set_index([('','Institutes'),dom_plans_matrix.columns]).T
      dom_plans_matrix.columns.names = ['Institution(s)','RCM']
    f.write(f'''<h3>{exp}</h3>
      <p style="font-size: smaller;"> Colour legend:
        <span class="planned">planned</span>
        <span class="running">running</span>
        <span class="completed">completed</span>
        <span class="published">published</span>
      </p>
    ''')
    f.write(dom_plans_matrix.style
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
