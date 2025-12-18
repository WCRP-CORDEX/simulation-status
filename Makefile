default:
	echo "You probably want to 'make update'"

update:
	python CMIP6_downscaling_plans.py
	python CORDEX_CMIP6_status.py
	python CORDEX_CMIP6_status_by_scenario.py
	python CORDEX_CMIP6_status_by_experiment.py
	python CORDEX_CMIP6_data_servers.py

update-cmip7:
	python CMIP7_downscaling_plans.py
	python CORDEX_CMIP7_status.py

update-esgf:
	python CORDEX_CMIP5_status_by_scenario.py

global-progress:
	python scripts/ecd_series.py
	python scripts/global_progress.py eval CMIP6
	python scripts/global_progress.py hist CMIP6
	python scripts/global_progress.py ssp CMIP6
	python scripts/global_progress.py ssp126 CMIP6
	python scripts/global_progress.py ssp370 CMIP6
	python scripts/global_progress.py ssp370 CMIP6 core
	python scripts/global_progress_map.py ssp CMIP6
	python scripts/global_progress_map.py ssp126 CMIP6
	python scripts/global_progress_map.py ssp370 CMIP6
	python scripts/global_progress_map.py ssp370 CMIP6 core
	