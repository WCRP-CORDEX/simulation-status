import pandas as pd
import yaml
from funs import html_header, html_footer, html_legend, table_props

collapse_institutions = True

plans = pd.read_csv('CMIP6_downscaling_plans.csv', na_filter=False)

with open('CORDEX_CMIP6_experiments.yaml') as fp:
  config = yaml.load(fp, Loader=yaml.FullLoader)

domains = config.keys()

f = open(f'docs/CORDEX_CMIP6_status_by_experiment.html','w')
f.write(html_header('CORDEX-CMIP6 experiment summary tables'))
f.write('<ul>')
[f.write(f'<li><a href="#{i}">{i}</a></li>') for i in domains]
f.write('</ul>')

d1 = dict(selector=".level1", props=table_props)
for domain in domains:
  dom_plans = plans[plans.domain == domain]
  tags = sorted(list(set(filter(lambda x: x.startswith('#'), dom_plans.comments.str.split(' ').agg(sum)))))
  dconf = config[domain] if domain in config else dict()
  if not tags:
    continue
  f.write(f'''<h2 id="{domain}">{domain}<a href="#top">^</a></h2>
    The following experiments contribute to CORDEX {domain} domain:
    <ul class="twocol">'''
  )
  [f.write(f'<li><a href="#{domain}-{i}">{dconf[i]["title"]}</a></li>') for i in dconf.keys()]
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
    df = df.assign(htmlstatus=pd.Series('<span sort="' + df.experiment +'" class="' + df.status + '">' + df.experiment + '</span>', index=df.index))
    df = df.assign(model_id=pd.Series(df.institute + '_' + df.rcm_name, index=df.index))
    column_id = 'rcm_name' if collapse_institutions else 'model_id'
    dom_plans_matrix = df.pivot_table(
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
      inst = df.drop_duplicates(subset=['institute','rcm_name']).pivot_table(
        index = ('driving_model', 'ensemble'),
        columns = 'rcm_name',
        values = 'institute',
        aggfunc = lambda x: ', '.join(sorted(x.dropna()))
      ).agg(lambda x: ', '.join(sorted(x.dropna())))
      inst.name = ('','Institutes')
      dom_plans_matrix = pd.concat([dom_plans_matrix, inst.to_frame().T])
      dom_plans_matrix = dom_plans_matrix.T.set_index([('','Institutes'),dom_plans_matrix.columns]).T
      dom_plans_matrix.columns.names = ['Institution(s)','RCM']
    title = tconf['title'] if 'title' in tconf else tag
    descr = tconf['description'] if 'description' in tconf else ''
    url = f'<p>URL: <a href="{tconf["url"]}">{tconf["url"]}</a>' if 'url' in tconf else ''
    f.write(f'''<h3 id="{domain}-{tag}">{title} <a href="#{domain}">^</a></h3>
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
       .render()
       .replace('nan','')
       .replace('historical','hist')
    )
    collapse_institutions = True
f.write(html_footer())
f.close()
