import pandas as pd

plans = pd.read_csv('CMIP6_downscaling_plans.csv', na_filter=False)

def addtag(word):
  rval = word
  if word.startswith('#'):
    rval = f'<span class="tag">{word[1:]}</span>'
  return(rval)

def taggify(text):
  return(' '.join([addtag(x) for x in text.split(' ')]))

fp = open('docs/CMIP6_downscaling_plans.html','w')
fp.write('''<!DOCTYPE html>
<html lang="en">
<head>
<meta name="author" content="J. Fernandez" />
<meta name="description" content="CORDEX CMIP6 downscaling plans" />
<meta name="keywords" content="HTML, CSS, JavaScript" />
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<link rel="stylesheet" type="text/css" href="https://cdn.datatables.net/1.11.5/css/jquery.dataTables.css">
<script type="text/javascript" charset="utf8" src="https://code.jquery.com/jquery-3.5.1.js"></script>
<script type="text/javascript" charset="utf8" src="https://cdn.datatables.net/1.11.5/js/jquery.dataTables.js"></script>
<script type="text/javascript">
$(document).ready( function () {
    $('#table_id').DataTable({
    });
} );
</script>
<title>CORDEX CMIP6 downscaling plans</title>
<style>
span.tag {
  background-color: #c5def5;
  padding: 0 10px;
  font-size: 12px;
  font-weight: 500;
  line-height: 22px !important;
  border: 1px solid transparent;
  border-radius: 2em;
}
</style>
</head>
<body>
<h1>CORDEX CMIP6 downscaling plans</h1>
<p>
This is an interactive table view of each of the CORDEX-CMIP6 simulations.
The table can be sorted by the different columns.
The search field can be used to filter the table.
Several terms can be entered (e.g. "evaluation completed" or "mpi ssp585") to show the rows matching all terms.
The table contents can be downloaded as a CSV file <a href="https://github.com/WCRP-CORDEX/simulation-status/raw/main/CMIP6_downscaling_plans.csv">here</a>.
To contribute/update simulations visit <a href="https://github.com/WCRP-CORDEX/simulation-status">https://github.com/WCRP-CORDEX/simulation-status</a>.
</p>
<table id="table_id" class="display">
    <thead>
        <tr>
''')
[fp.write(f'              <th>{col}</th>\n') for col in plans]
fp.write(f'''
        </tr>
    </thead>
    <tbody>
''')
for idx, plan in plans.iterrows():
  fp.write(f'        <tr>\n')
  [fp.write(f'            <td>{taggify(item)}</td>\n') for item in plan]
  fp.write(f'        </tr>\n')
fp.write('''
    </tbody>
</table>
</body>
</html>
''')
fp.close()
