import datetime
import pandas as pd
from funs import *

csv2datatable(
  'CMIP6_downscaling_plans.csv',
  'docs/CMIP6_downscaling_plans.html',
  title = 'CORDEX CMIP6 downscaling plans',
  intro = f'''
<div style="display:table;width:100%;">
  <div style="display:table-row;">
    <div style="display:table-cell;width:50%;">
      <a href="https://wcrp-cordex.github.io/simulation-status">Back to main</a>, see
      <a href="./CMIP6_downscaling_plans.html">full list</a>, or see tables by 
      <a href="./CORDEX_CMIP6_status.html">domain</a>,
      <a href="./CORDEX_CMIP6_status_by_scenario.html">scenario</a> or
      <a href="./CORDEX_CMIP6_status_by_experiment.html">experiment</a>
    </div>
    <div style="display:table-cell;text-align:right;width:50%;">
      (Version: {datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M")} UTC)
    </div>
  </div>
</div>
<p>
This is an interactive table view of each of the CORDEX-CMIP6 simulations.
The table can be sorted by the different columns.
The search field can be used to filter the table.
Several terms can be entered (e.g. "evaluation completed" or "mpi ssp585") to show the rows matching all terms.
The table contents can be downloaded as a CSV file <a href="https://github.com/WCRP-CORDEX/simulation-status/raw/main/CMIP6_downscaling_plans.csv">here</a>.
To contribute/update simulations open an issue or pull request at <a href="https://github.com/WCRP-CORDEX/simulation-status">https://github.com/WCRP-CORDEX/simulation-status</a>.
</p>
''',
  rename_fields = {
    'estimated_completion_date': 'ECD',
    'driving_variant_label': 'variant',
    'driving_experiment_id': 'experiment'
  }
)
