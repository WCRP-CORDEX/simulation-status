#!/usr/bin/env python3
import pandas as pd
from funs import html_header, html_footer, html_legend, table_props

df = pd.read_csv('CMIP6_downscaling_plans.csv')

# Drop unnecessary columns
df.drop(
  ['contact', 'estimated_completion_date', 'comments'],
  axis = 'columns', inplace = True
)
df.drop_duplicates(inplace = True)

collapse_institutions = True

domain_ids = sorted(list(set(df.domain_id)))

f = open(f'docs/CORDEX_CMIP6_status_by_scenario.html','w')
f.write(html_header('CORDEX-CMIP6 downscaling plans summary tables (split by SSP)'))
f.write('<p style="text-align:left"> Domains: | ')
[f.write(f'<a href="#{dom}">{dom}</a> | ') for dom in domain_ids]
d1 = dict(selector=".level0", props=table_props)
for domain_id in domain_ids:
  f.write(f'''<h2 id="{domain_id}">{domain_id}</h2>''')
  for exp in ['ssp119', 'ssp126', 'ssp245', 'ssp370', 'ssp585']:
    dom_df = df[(df.domain_id == domain_id) & (df.driving_experiment_id == exp)]
    dom_df = dom_df.assign(htmlstatus=pd.Series('<span class="' + dom_df.status + '">' + dom_df.driving_experiment_id + '</span>', index=dom_df.index))
    dom_df = dom_df.assign(instmodel=pd.Series(dom_df.institution_id + '-' + dom_df.source_id, index=dom_df.index))
    column_id = 'source_id' if collapse_institutions else 'instmodel'
    dom_plans_matrix = dom_df.pivot_table(
      index = ('driving_source_id', 'driving_variant_label'),
      columns = column_id,
      values = 'htmlstatus',
      aggfunc = lambda x: ' '.join(x.dropna())
    )
    if collapse_institutions:
      inst = dom_df.drop_duplicates(subset=['institution_id','source_id']).pivot_table(
        index = ('driving_source_id', 'driving_variant_label'),
        columns = 'source_id',
        values = 'institution_id',
        aggfunc = lambda x: ', '.join(x.dropna())
      ).agg(lambda x: ', '.join(x.dropna()))
      inst.name = ('','Institutes')
      dom_plans_matrix = pd.concat([dom_plans_matrix, inst.to_frame().T])
      dom_plans_matrix = dom_plans_matrix.T.set_index([('','Institutes'),dom_plans_matrix.columns]).T
      dom_plans_matrix.columns.names = ['Institution(s)','RCM']
    f.write(f'<h3>{exp}</h3>\n{html_legend}')
    f.write(dom_plans_matrix.style
       .set_properties(**{'font-size':'8pt', 'border':'1px lightgrey solid !important'})
       .set_table_styles([d1,{
          'selector': 'th',
          'props': [('font-size', '8pt'),('border-style','solid'),('border-width','1px')]
        }])
       .to_html()
       .replace('nan','')
       .replace('historical','hist')
    )
f.write(html_footer())
f.close()
