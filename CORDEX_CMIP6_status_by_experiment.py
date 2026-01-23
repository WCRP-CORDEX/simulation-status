import numpy as np
import pandas as pd
import yaml
from funs import html_header, html_footer, html_legend, table_props

collapse_institutions = True

plans = pd.read_csv('CMIP6_downscaling_plans.csv', na_filter=False)

with open('CORDEX_CMIP6_experiments.yaml') as fp:
  config = yaml.load(fp, Loader=yaml.FullLoader)

domain_ids = config.keys()

f = open(f'docs/CORDEX_CMIP6_status_by_experiment.html','w')
f.write(html_header('CORDEX-CMIP6 experiment summary tables', mip_era='CMIP6'))
f.write('<ul>')
[f.write(f'<li><a href="#{i}">{i}</a></li>') for i in domain_ids]
f.write('</ul>')

def source_id_to_family(plansdf): 
  family_mapping = {
    'CCAM': ['CCAM','CCAM-2203','CCAM-exp2017','CCAM-exp2021','CCAM-v2105','CCAM-v2112','CCAMoc-v2112'],
    'CCLM': ['CCLM5-0-9-NEMOMED12-3-6','CCLM6-0-1','CCLM6-0-1-URB', 'COSMO-CLM5-0-9', 'GCOAST-AHOI1-1','GCOAST-AHOIB1-1', 'TSMP1-140-E'],
    'CNRM-ALADIN': ['CNRM-ALADIN64E1','CNRM-ALADIN64P1','CNRM-RCSM6B', 'RCSM6'],
    'ICON': ['ICON-CLM-202407-1-1', 'GCOAST-AHOI2-1','ICON-CLM','ICON-OASIS-NEMO', 'ROAM-NBS'],
    'RACMO': ['RACMO23E','RACMO24P'],
    'HadRM': ['HadGEM3-RA','HadREM3-GA7-05'],
    'REMO': ['REMO2020-2-2-iMOVE','REMO2020-2-2-iMOVE-LUC','REMO2020-2-2'],
    'RegCM': ['RegCM-ES','RegCM4-6','RegCM4-NH','RegCM4-NH-exp16','RegCM5','RegCM5-0','RegCM5-exp16'],
    'WRF': ['WRF-R3','WRF400','WRF412C1','WRF451Q', 'WRF461S-SN', 'WRF461T-SN','RegIPSL', 'WRF461U']
  }
  model_to_family = {model: family for family, models in family_mapping.items() for model in models}
  plansdf['source_id'] = plansdf['source_id'].apply(lambda x: model_to_family.get(x, x))
  return(plansdf)

d1 = dict(selector=".level1", props=table_props)
for domain_id in domain_ids:
  dom_plans = plans[plans.domain_id == domain_id] if domain_id != 'All' else source_id_to_family(plans.copy())
  tags = sorted(list(set(filter(lambda x: x.startswith('#'), dom_plans.comments.str.split(' ').agg('sum')))))
  dconf = config[domain_id] if domain_id in config else dict()
  if not tags:
    continue
  f.write(f'''<h2 id="{domain_id}">{domain_id}<a href="#top">^</a></h2>
    The following experiments contribute to CORDEX {domain_id} domain:
    <ul class="twocol">'''
  )
  [f.write(f'<li><a href="#{domain_id}-{i}">{dconf[i]["title"]}</a></li>') for i in dconf.keys()]
  f.write('</ul>')
  for tag in dconf.keys():
    tconf = dconf[tag]
    if 'condition' in tconf:
      df = dom_plans.copy()
      for cond in tconf['condition']:
        if cond.startswith('tag:'):
          df = df[df.comments.str.contains('#'+cond[4:], case=False, na=False)]
        else:
          df = df.query(cond)
    else:
      df = dom_plans[dom_plans.comments.str.contains(tag, case=False, na=False)]
    if df.empty:
      continue
    collapse_institutions = tconf['collapse_institutions'] if 'collapse_institutions' in tconf else collapse_institutions
    df = df.assign(htmlstatus=pd.Series('<span sort="' + df.driving_experiment_id +'" class="' + df.status + '">' + df.driving_experiment_id + '</span>', index=df.index))
    df = df.assign(model_id=pd.Series(df.institution_id + '_' + df.source_id, index=df.index))
    column_id = 'source_id' if collapse_institutions else 'model_id'
    row_headers = ('driving_source_id', 'driving_variant_label') if domain_id != 'All' else ('domain_id', 'driving_source_id', 'driving_variant_label')
    dom_plans_matrix = df.pivot_table(
      index = row_headers,
      columns = column_id,
      values = 'htmlstatus',
      aggfunc = lambda x: ' '.join(sorted(x.dropna()))
    )
    # Bring ERA5 to the top
    era5_mask = dom_plans_matrix.index.get_level_values('driving_source_id') == 'ERA5'
    dom_plans_matrix = dom_plans_matrix.iloc[list(np.where(era5_mask)[0]) + list(np.where(~era5_mask)[0])]

    if collapse_institutions:
      inst = df.drop_duplicates(subset=['institution_id','source_id']).pivot_table(
        index = row_headers,
        columns = 'source_id',
        values = 'institution_id',
        aggfunc = lambda x: ', '.join(sorted(x.dropna()))
      ).agg(lambda x: ', '.join(sorted(x.dropna())))
      new_columns = pd.MultiIndex.from_arrays([inst.values, dom_plans_matrix.columns])
      dom_plans_matrix.columns = new_columns
      dom_plans_matrix.columns.names = ['Institution(s)', 'RCM']

    title = tconf['title'] if 'title' in tconf else tag
    descr = tconf['description'] if 'description' in tconf else ''
    url = f'<p>URL: <a href="{tconf["url"]}">{tconf["url"]}</a>' if 'url' in tconf else ''
    f.write(f'''<h3 id="{domain_id}-{tag}">{title} <a href="#{domain_id}">^</a></h3>
      <p> {descr}
      {url}
      {html_legend}
    ''')

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
    collapse_institutions = True
f.write(html_footer())
f.close()
