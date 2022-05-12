import pandas as pd

def addtag(word):
  rval = word
  if word.startswith('#'):
    rval = f'<span class="tag">{word[1:]}</span>'
  if word.startswith('http'):
    rval = f'<a href="{word}">{word}</a>'
  return(rval)

def taggify(text):
  return(' '.join([addtag(x) for x in text.split(' ')]))

def csv2datatable(csvfile, htmlout, title='', intro=''):
  plans = pd.read_csv(csvfile, na_filter=False)
  fp = open(htmlout,'w')
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
''')
  if title:
    fp.write(f'<title>{title}</title>')
  fp.write('''
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
</html>''')
  fp.close()
