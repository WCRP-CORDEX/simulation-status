default:
	echo "You probably want to 'make update'"

update:
	python3 CMIP6_downscaling_plans.py
	python3 CORDEX_CMIP6_status.py
	python3 CORDEX_CMIP6_status_by_scenario.py
	python3 CORDEX_CMIP6_status_by_experiment.py

update-esgf:
	python3 CORDEX_CMIP5_status_by_scenario.py
