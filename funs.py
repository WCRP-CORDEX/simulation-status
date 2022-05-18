import pandas as pd

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

def csv2datatable(csvfile, htmlout, title='', intro='', rename_fields = {}):
  plans = pd.read_csv(csvfile, na_filter=False)
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
span.selected {color: #3399FF}
span.planned {color: #FF9999}
span.running {color: #009900}
span.completed {color: black; font-weight: bold}
span.published {color: #3399FF; font-weight: bold}
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
