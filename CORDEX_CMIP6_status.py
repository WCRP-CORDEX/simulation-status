import pandas as pd
from funs import html_header, html_footer, html_legend, table_props
from funs import add_registration_info, generate_domain_table, load_cmip6_plans_with_publication_overlay

collapse_institutions = True

plans = load_cmip6_plans_with_publication_overlay('CMIP6_downscaling_plans.csv')
plans = add_registration_info(plans, cmip_era='CMIP6')
plans = plans.assign(domain=plans.domain_id.str.split('-', n=1).str[0])
domain_ids = sorted(list(set(plans.domain_id)))
domains = sorted(list(set(plans.domain)))

f = open(f'docs/CORDEX_CMIP6_status.html','w')
f.write(html_header('CORDEX-CMIP6 downscaling plans summary tables', mip_era='CMIP6'))
f.write('<p style="text-align:left"> Domains: |')
[f.write(f'<a href="#{dom}">{dom}</a> | ') for dom in domain_ids]
f.write('<br>All resolutions: |')
[f.write(f'<a href="#all-{dom}">{dom}</a> | ') for dom in domains]
d1 = dict(selector=".level1", props=table_props)

def write_domain_table(domain_id, dom_plans, anchor_id=None, heading='h2'):
  dom_plans_matrix = generate_domain_table(dom_plans, collapse_institutions)
  anchor_id = anchor_id or domain_id
  f.write(f'<{heading} id="{anchor_id}">{domain_id}<a href="#top">^</a></{heading}>\n{html_legend}')
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

for domain_id in domain_ids:
  dom_plans = plans[plans.domain_id == domain_id]
  write_domain_table(domain_id, dom_plans)

f.write('<h2 id="all-resolutions">All resolutions</h2>\n')
for domain in domains:
  dom_plans = plans[plans.domain == domain]
  write_domain_table(domain, dom_plans, anchor_id=f'all-{domain}', heading='h3')

f.write(html_footer())
f.close()
