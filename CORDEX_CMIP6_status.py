import pandas as pd
import requests
from funs import html_header, html_footer, html_legend, table_props
from icecream import ic

collapse_institutions = True

plans = pd.read_csv('CMIP6_downscaling_plans.csv', na_filter=False)

# Cross with registration info
url_source_id = "https://raw.githubusercontent.com/WCRP-CORDEX/cordex-cmip6-cv/refs/heads/main/CORDEX-CMIP6_source_id.json"
response = requests.get(url_source_id)
response.raise_for_status()
source_ids = response.json()["source_id"]
source_type_map = {key: value["source_type"] for key, value in source_ids.items()}
plans["registered"] = plans["source_id"].apply(lambda x: x in source_type_map)
plans["source_type"] = plans["source_id"].apply(lambda x: source_type_map.get(x, "") if x in source_type_map else "unregistered")

url_institution_id = "https://raw.githubusercontent.com/WCRP-CORDEX/cordex-cmip6-cv/refs/heads/main/CORDEX-CMIP6_institution_id.json"
response = requests.get(url_institution_id)
response.raise_for_status()
institution_ids = response.json()["institution_id"]
plans["inst_registered"] = plans["institution_id"].apply(lambda x: "reginst" if x in institution_ids else "unreginst")

domain_ids = sorted(list(set(plans.domain_id)))

f = open(f'docs/CORDEX_CMIP6_status.html','w')
f.write(html_header('CORDEX-CMIP6 downscaling plans summary tables'))
f.write('<p style="text-align:left"> Domains: |')
[f.write(f'<a href="#{dom}">{dom}</a> | ') for dom in domain_ids]
d1 = dict(selector=".level1", props=table_props)
for domain_id in domain_ids:
  dom_plans = plans[plans.domain_id == domain_id]
  dom_plans = dom_plans.assign(htmlstatus=pd.Series('<span sort="' + dom_plans.driving_experiment_id +'" class="' + dom_plans.status + '">' + dom_plans.driving_experiment_id + '</span>', index=dom_plans.index))
  dom_plans = dom_plans.assign(source_id=pd.Series('<span sort="' + dom_plans.source_id +'" class="' + dom_plans.source_type + '">' + dom_plans.source_id + '</span>', index=dom_plans.index))
  dom_plans = dom_plans.assign(institution_id=pd.Series('<span sort="' + dom_plans.institution_id +'" class="' + dom_plans.inst_registered + '">' + dom_plans.institution_id + '</span>', index=dom_plans.index))
  dom_plans = dom_plans.assign(model_id=pd.Series(dom_plans.institution_id + '-' + dom_plans.source_id, index=dom_plans.index))
  column_id = 'source_id' if collapse_institutions else 'model_id'
  dom_plans_matrix = dom_plans.pivot_table(
    index = ('driving_source_id', 'driving_variant_label'),
    columns = column_id,
    values = 'htmlstatus',
    aggfunc = lambda x: ' '.join(sorted(x.dropna()))
  )
  dom_plans_matrix = pd.concat([  # Bring ERA5 to the top
    dom_plans_matrix.query("driving_source_id == 'ERA5'"),
    dom_plans_matrix.drop(('ERA5',''), axis=0, errors='ignore')
  ], axis=0)
  if collapse_institutions:
    inst = dom_plans.drop_duplicates(subset=['institution_id','source_id']).pivot_table(
      index = ('driving_source_id', 'driving_variant_label'),
      columns = 'source_id',
      values = 'institution_id',
      aggfunc = lambda x: ', '.join(x.dropna())
    ).agg(lambda x: ', '.join(x.dropna()))
    inst.name = ('','Institutes')
    dom_plans_matrix = pd.concat([dom_plans_matrix, inst.to_frame().T])
    dom_plans_matrix = dom_plans_matrix.T.set_index([('','Institutes'),dom_plans_matrix.columns]).T
    dom_plans_matrix.columns.names = ['Institution(s)','RCM']
  f.write(f'<h2 id="{domain_id}">{domain_id}<a href="#top">^</a></h2>\n{html_legend}')
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
