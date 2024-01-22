import pandas as pd
from funs import html_header, html_footer, html_legend, table_props

collapse_institutions = True

plans = pd.read_csv('CMIP6_downscaling_plans.csv', na_filter=False)
domains = sorted(list(set(plans.domain)))

f = open(f'docs/CORDEX_CMIP6_status.html','w')
f.write(html_header('CORDEX-CMIP6 downscaling plans summary tables'))
f.write('<p style="text-align:left"> Domains: |')
[f.write(f'<a href="#{dom}">{dom}</a> | ') for dom in domains]
d1 = dict(selector=".level1", props=table_props)
for domain in domains:
  dom_plans = plans[plans.domain == domain]
  dom_plans = dom_plans.assign(htmlstatus=pd.Series('<span sort="' + dom_plans.experiment +'" class="' + dom_plans.status + '">' + dom_plans.experiment + '</span>', index=dom_plans.index))
  dom_plans = dom_plans.assign(model_id=pd.Series(dom_plans.institute + '-' + dom_plans.rcm_name, index=dom_plans.index))
  column_id = 'rcm_name' if collapse_institutions else 'model_id'
  dom_plans_matrix = dom_plans.pivot_table(
    index = ('driving_model', 'ensemble'),
    columns = column_id,
    values = 'htmlstatus',
    aggfunc = lambda x: ' '.join(sorted(x.dropna()))
  )
  dom_plans_matrix = pd.concat([  # Bring ERA5 to the top
    dom_plans_matrix.query("driving_model == 'ERA5'"),
    dom_plans_matrix.drop(('ERA5',''), axis=0, errors='ignore')
  ], axis=0)
  if collapse_institutions:
    inst = dom_plans.drop_duplicates(subset=['institute','rcm_name']).pivot_table(
      index = ('driving_model', 'ensemble'),
      columns = 'rcm_name',
      values = 'institute',
      aggfunc = lambda x: ', '.join(x.dropna())
    ).agg(lambda x: ', '.join(x.dropna()))
    inst.name = ('','Institutes')
    dom_plans_matrix = pd.concat([dom_plans_matrix, inst.to_frame().T])
    dom_plans_matrix = dom_plans_matrix.T.set_index([('','Institutes'),dom_plans_matrix.columns]).T
    dom_plans_matrix.columns.names = ['Institution(s)','RCM']
  f.write(f'<h2 id="{domain}">{domain}<a href="#top">^</a></h2>\n{html_legend}')
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
f.write(html_footer())
f.close()
