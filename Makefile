default:
	echo "You probably want to 'make update'"

update:
	python CMIP6_downscaling_plans.py
	python CORDEX_CMIP6_status.py
	python CORDEX_CMIP6_status_by_scenario.py
	python CORDEX_CMIP6_status_by_experiment.py
	python CORDEX_CMIP6_data_servers.py

update-esgf:
	python CORDEX_CMIP5_status_by_scenario.py

global-progress:
	python ecd_series.py
	python global_progress.py eval CMIP6
	python global_progress.py hist CMIP6
	python global_progress.py ssp CMIP6
