import datetime
import pandas as pd

collapse_institutions = True

plans = pd.read_csv('CMIP6_downscaling_plans.csv', na_filter=False)
domains = sorted(list(set(plans.domain)))

f = open(f'docs/CORDEX_CMIP6_status.html','w')
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
<h1 id="top"> CORDEX-CMIP6 downscaling plans summary tables</h1>
<p style="text-align: right;">(Version: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M")})</p>
<p style="text-align: justify;">
Simulation status according to CORDEX-CMIP6 downscaling plans reported by the groups and collected in <a href="https://github.com/WCRP-CORDEX/simulation-status/blob/main/CMIP6_downscaling_plans.csv">CMIP6_downscaling_plans.csv</a>. Check that file for further details.
To contribute/update simulations use this <a href="https://docs.google.com/document/d/1Jy53yvB9SDOiWcwKRJc_HpWVgmjxZhy-qVviHl6ymDM/edit?usp=sharing">Google doc</a>.
<p style="text-align:left"> Domains: |
''')
[f.write(f'<a href="#{dom}">{dom}</a> | ') for dom in domains]
d1 = dict(selector=".level0", props=[('min-width', '130px')])
for domain in domains:
  dom_plans = plans[plans.domain == domain]
  dom_plans = dom_plans.assign(htmlstatus=pd.Series('<span class="' + dom_plans.status + '">' + dom_plans.experiment + '</span>', index=dom_plans.index))
  dom_plans = dom_plans.assign(model_id=pd.Series(dom_plans.institute + '-' + dom_plans.rcm_name, index=dom_plans.index))
  column_id = 'rcm_name' if collapse_institutions else 'model_id'
  dom_plans_matrix = dom_plans.pivot_table(
    index = ('driving_model', 'ensemble'),
    columns = column_id,
    values = 'htmlstatus',
    aggfunc = lambda x: ' '.join(x.dropna())
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
    dom_plans_matrix = dom_plans_matrix.append(inst)
    dom_plans_matrix = dom_plans_matrix.T.set_index([('','Institutes'),dom_plans_matrix.columns]).T
    dom_plans_matrix.columns.names = ['Institution(s)','RCM']
  f.write(f'''<h2 id="{domain}">{domain}<a href="#top">^</a></h2>
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
