import pandas as pd
from funs import *

csv2datatable(
  'CMIP6_downscaling_plans.csv',
  'docs/CMIP6_downscaling_plans.html',
  title = 'CORDEX CMIP6 downscaling plans',
  intro = '''
<p>
This is an interactive table view of each of the CORDEX-CMIP6 simulations.
The table can be sorted by the different columns.
The search field can be used to filter the table.
Several terms can be entered (e.g. "evaluation completed" or "mpi ssp585") to show the rows matching all terms.
The table contents can be downloaded as a CSV file <a href="https://github.com/WCRP-CORDEX/simulation-status/raw/main/CMIP6_downscaling_plans.csv">here</a>.
To contribute/update simulations visit <a href="https://github.com/WCRP-CORDEX/simulation-status">https://github.com/WCRP-CORDEX/simulation-status</a>.
</p>
''',
  rename_fields = {'estimated_completion_date': 'ECD'}
)
