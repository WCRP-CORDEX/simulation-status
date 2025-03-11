import datetime
import pandas as pd

span_style = '''
span.planned {color: #F54d4d; font-weight: bold}
span.running {color: #009900; font-weight: bold}
span.completed {color: #17202a; font-weight: bold}
span.published {color: #3399FF; font-weight: bold}

span.reginst {color: black; font-weight: bold}
span.unreginst {color: grey; font-style: italic; font-weight: bold}
span.unregistered {color: grey; font-style: italic; font-weight: bold}
span.ARCM {color: black; font-weight: bold}
span.AORCM {color: #2980b9; font-weight: bold}
span.AGCM {color: black; font-weight: bold}
span.AOGCM {color: #2980b9; font-weight: bold}
span.ESD {color: #ca6f1e; font-weight: bold}
'''

html_style = '''
<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700&display=swap" rel="stylesheet">
<style>
body {
  font-family: 'Montserrat', sans-serif;
  padding-top: 15px;
  padding-left: 15px;
  padding-right: 15px;
  padding-bottom: 600px;
}
tr:hover {background-color:#f5f5f5;}
th, td {text-align: center; padding: 3px;}
table {border-collapse: collapse;}''' + span_style + '''
a {color: DodgerBlue}
a:link { text-decoration: none; }
a:visited { text-decoration: none; }
a:hover { text-decoration: underline; }
a:active { text-decoration: underline;}
ul.twocol { columns: 2; -webkit-columns: 2; -moz-columns: 2; }
.logo {
  text-align: center;
  margin-bottom: 20px;
}
</style>
'''

html_legend = '''
      <p style="font-size: smaller;"> Colour legend for status:
        (
        <span class="planned">planned</span>
        <span class="running">running</span>
        <span class="completed">completed</span>
        <span class="published">published</span>
        )
        //
        source_type:
        (
        <span class="unregistered">unregistered</span>
        <span class="ARCM">ARCM</span>
        <span class="AORCM">AORCM</span>
        <span class="ESD">ESD</span>
        )
      </p>
'''

table_props = [('width', '100px')]

def html_header(title = 'CORDEX-CMIP6 downscaling plans'):
  return(f'''<!DOCTYPE html>
<html><head>
{html_style}
</head><body>
<div class="logo">
<img src="https://cordex.org/wp-content/uploads/2025/02/CORDEX_RGB_logo_baseline_positive-300x133.png" 
   alt="CORDEX Logo" >
<h1 id="top">{title}</h1>
</div>
<div style="display:table;width:100%;">
  <div style="display:table-row;">
    <div style="display:table-cell;width:50%;">
      <a href="https://wcrp-cordex.github.io/simulation-status">Back to main</a> or see tables by 
      <a href="./CORDEX_CMIP6_status.html">domain</a>,
      <a href="./CORDEX_CMIP6_status_by_scenario.html">scenario</a> or
      <a href="./CORDEX_CMIP6_status_by_experiment.html">experiment</a>
    </div>
    <div style="display:table-cell;text-align:right;width:50%;">
      (Version: {datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M")} UTC)
    </div>
  </div>
</div>
<p style="text-align: justify;">
Simulation status according to CORDEX-CMIP6 downscaling plans reported by the groups and collected in <a href="https://github.com/WCRP-CORDEX/simulation-status/blob/main/CMIP6_downscaling_plans.csv">CMIP6_downscaling_plans.csv</a>. 
To contribute/update simulations open and issue or pull request at <a href="https://github.com/WCRP-CORDEX/simulation-status">https://github.com/WCRP-CORDEX/simulation-status</a>.
'''
  )

def html_footer():
  return('</body></html>')

def addtag(word, field):
  rval = word
  if (field == 'comments') and word.startswith('#'):
    rval = f'<span class="tag">{word[1:]}</span>'
  elif (field == 'comments') and word.startswith('http'):
    rval = f'<a href="{word}">{word}</a>'
  elif (field == 'status') and word in ['selected', 'planned', 'running', 'completed', 'published']:
    rval = f'<span class="{word}">{word}</span>'
  return(rval)

def taggify(text, field):
  rval = text
  if field in ['status', 'comments']:
    rval = ' '.join([addtag(x, field) for x in text.split(' ')])
  return(rval)

def csv2datatable(csvfile, htmlout, title='', intro='', rename_fields = {}, column_as_link="", column_as_link_source=""):
  plans = pd.read_csv(csvfile, na_filter=False)
  if column_as_link:
    if not column_as_link_source:
      column_as_link_source = column_as_link
    plans[column_as_link] = (
      '<a href="' + plans[column_as_link_source] + '">' + plans[column_as_link] + "</a>"
    )
  if column_as_link != column_as_link_source:
    plans.drop(columns=column_as_link_source, inplace=True)

  field_names = dict(zip(plans.columns,plans.columns))
  field_names.update(rename_fields)
  fp = open(htmlout,'w')
  fp.write('''<!DOCTYPE html>
<html lang="en">
<head>
<meta name="author" content="J. Fernandez" />
<meta name="keywords" content="HTML, CSS, JavaScript" />
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<link rel="stylesheet" type="text/css" href="https://cdn.datatables.net/1.11.5/css/jquery.dataTables.css">
<script type="text/javascript" charset="utf8" src="https://code.jquery.com/jquery-3.5.1.js"></script>
<script type="text/javascript" charset="utf8" src="https://cdn.datatables.net/1.11.5/js/jquery.dataTables.js"></script>
<script type="text/javascript" charset="utf8" src="https://cdn.datatables.net/plug-ins/2.0.5/features/deepLink/dataTables.deepLink.min.js"></script>
<script type="text/javascript">
$(document).ready( function () {
    $('#table_id').DataTable( $.fn.dataTable.ext.deepLink( [
      'search.search'
    ]));
} );
</script>
''')
  if title:
    fp.write(f'<title>{title}</title>')
  fp.write(f'''
<style>
span.tag {{
  background-color: #c5def5;
  padding: 0 10px;
  font-size: 12px;
  font-weight: 500;
  line-height: 22px !important;
  border: 1px solid transparent;
  border-radius: 2em;
}}
a {{color: DodgerBlue}}
a:link {{ text-decoration: none; }}
a:visited {{ text-decoration: none; }}
a:hover {{ text-decoration: underline; }}
a:active {{ text-decoration: underline;}}
{span_style}
</style>
</head>
<body>
''')
  if title:
    fp.write(f'<h1>{title}</h1>')
  if intro:
    fp.write(f'{intro}')
  fp.write('''
<table id="table_id" class="display">
    <thead>
        <tr>
''')
  [fp.write(f'              <th>{field_names[x]}</th>\n') for x in plans]
  fp.write(f'''
        </tr>
    </thead>
    <tbody>
''')
  for idx, plan in plans.iterrows():
    fp.write(f'        <tr>\n')
    for field,item in zip(plans.columns, plan):
      fp.write(f'            <td>{taggify(item, field)}</td>\n')
    fp.write(f'        </tr>\n')
  fp.write('''
    </tbody>
</table>
</body>
</html>''')
  fp.close()
