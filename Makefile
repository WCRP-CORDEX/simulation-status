default:
	echo "You probably want to 'make update'"

update:
	python CMIP6_downscaling_plans.py
	python CORDEX_CMIP6_status.py
	python CORDEX_CMIP6_status_by_scenario.py
	python CORDEX_CMIP6_status_by_experiment.py

update-esgf:
	python CORDEX_CMIP5_status_by_scenario.py
