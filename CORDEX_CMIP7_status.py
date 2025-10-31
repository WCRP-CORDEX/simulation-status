import pandas as pd
from funs import html_header, html_footer, html_legend, table_props
from funs import add_registration_info, generate_domain_table

collapse_institutions = True

plans = pd.read_csv('CMIP7_downscaling_plans.csv', na_filter=False)
plans = add_registration_info(plans, cmip_era='CMIP7')
domain_ids = sorted(list(set(plans.domain_id)))

f = open(f'docs/CORDEX_CMIP7_status.html','w')
f.write(html_header('CORDEX-CMIP7 downscaling plans summary tables'))
f.write('<p style="text-align:left"> Domains: |')
[f.write(f'<a href="#{dom}">{dom}</a> | ') for dom in domain_ids]
d1 = dict(selector=".level1", props=table_props)
for domain_id in domain_ids:
  dom_plans = plans[plans.domain_id == domain_id]
  dom_plans_matrix = generate_domain_table(dom_plans, collapse_institutions)
  
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
