#!/usr/bin/env python3
import pandas as pd

from funs import (
  CMIP6_SIMULATION_KEYS,
  apply_cmip6_publication_overlay,
  get_cmip6_stac_publication_table,
)


if __name__ == '__main__':
  publication = get_cmip6_stac_publication_table(paginate=True, limit=1000)
  publication = publication.assign(status='published')

  ordered_columns = [
    'domain_id',
    'institution_id',
    'source_id',
    'driving_source_id',
    'driving_variant_label',
    'driving_experiment_id',
    'status',
    'estimated_completion_date',
    'data_node',
    'n_datasets',
  ]
  published = publication[ordered_columns].sort_values(CMIP6_SIMULATION_KEYS)

  published.to_csv('CMIP6_downscaling_published.csv', index=False)
  print('Wrote CMIP6_downscaling_published.csv')
  print(f'STAC published simulations: {len(published)}')

  plans = pd.read_csv('CMIP6_downscaling_plans.csv', na_filter=False)
  merged = apply_cmip6_publication_overlay(plans, publication, report_missing=True)
  merged.to_csv('CMIP6_downscaling_plans_merged.csv', index=False)
  print('Wrote CMIP6_downscaling_plans_merged.csv')
