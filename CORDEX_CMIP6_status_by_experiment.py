import datetime
import pandas as pd
import yaml

collapse_institutions = True

plans = pd.read_csv('CMIP6_downscaling_plans.csv', na_filter=False)

with open('CORDEX_CMIP6_experiments.yaml') as fp:
  config = yaml.load(fp, Loader=yaml.FullLoader)

domains = config.keys()

f = open(f'docs/CORDEX_CMIP6_status_by_experiment.html','w')
f.write(f'''<!DOCTYPE html>
<html><head>
<style>
body {{ padding-bottom: 600px; }}
tr:hover {{background-color:#f5f5f5;}}
th, td {{text-align: center; padding: 3px;}}
table {{border-collapse: collapse;}}
span.planned {{color: #F54d4d; font-weight: bold}}
span.running {{color: #009900; font-weight: bold}}
span.completed {{color: black; font-weight: bold}}
span.published {{color: #3399FF; font-weight: bold}}
a {{color: DodgerBlue}}
a:link {{ text-decoration: none; }}
a:visited {{ text-decoration: none; }}
a:hover {{ text-decoration: underline; }}
a:active {{ text-decoration: underline;}}
ul.twocol {{ columns: 2; -webkit-columns: 2; -moz-columns: 2; }}
</style>
</head><body>
<h1 id="top"> CORDEX-CMIP6 experiment summary tables</h1>
<p style="text-align: right;">(Version: {datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")})</p>
<p style="text-align: justify;">
Simulation status for different experiments within domains, as collected from the CORDEX-CMIP6 downscaling plans reported by the groups in <a href="https://github.com/WCRP-CORDEX/simulation-status/blob/main/CMIP6_downscaling_plans.csv">CMIP6_downscaling_plans.csv</a>. Check that file for further details. Experiment descriptions are provided at <a href="https://github.com/WCRP-CORDEX/simulation-status/blob/main/CORDEX_CMIP6_experiments.yaml">CORDEX_CMIP6_experiments.yaml</a>.
To contribute/update simulations use this <a href="https://docs.google.com/document/d/1Jy53yvB9SDOiWcwKRJc_HpWVgmjxZhy-qVviHl6ymDM/edit?usp=sharing">Google doc</a>.
<p style="text-align: justify;">
See also other views of these simulations as a single table <a href="https://wcrp-cordex.github.io/simulation-status/CORDEX_CMIP6_status.html">per domain</a> or <a href="https://wcrp-cordex.github.io/simulation-status/CORDEX_CMIP6_status_by_scenario.html">per SSP</a>.
<ul>
''')

[f.write(f'<li><a href="#{i}">{i}</a></li>') for i in domains]

f.write(f'''
</ul>
''')

d1 = dict(selector=".level0", props=[('min-width', '130px')])
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
    df = df.assign(model_id=pd.Series(df.institute + '-' + df.rcm_name, index=df.index))
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
      dom_plans_matrix = pd.concat([dom_plans_matrix, inst])
      dom_plans_matrix = dom_plans_matrix.T.set_index([('','Institutes'),dom_plans_matrix.columns]).T
      dom_plans_matrix.columns.names = ['Institution(s)','RCM']
    title = tconf['title'] if 'title' in tconf else tag
    descr = tconf['description'] if 'description' in tconf else ''
    url = f'<p>URL: <a href="{tconf["url"]}">{tconf["url"]}</a>' if 'url' in tconf else ''
    f.write(f'''<h3 id="{domain}-{tag}">{title} <a href="#{domain}">^</a></h3>
      <p> {descr}
      {url}
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
    collapse_institutions = True
f.write('</body></html>')
f.close()
