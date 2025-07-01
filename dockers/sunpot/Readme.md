## Calculating Solar Potentials and Saving Into CityDB v5

- Solar potential calculations depend on environment variables generated dynamically using the `generate-env` script.
- This script reads from `config-sunpot.yml`, `config-base.yml`, and `config-loader.yml`, and also automates Docker login for the `sunpot` image.
- After generating the environment variables and ensuring CityDB v5 is running, you can start the `sunpot` service. It performs calculations using CityDB v4 and then imports the results into CityDB v5.


