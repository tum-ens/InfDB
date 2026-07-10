# Linear Heat Density Use Case

Within the linear heat density demo, we illustrate how to leverage the InfDB platform to estimate the linear heat density of streets as a key metric for assessing the feasibility and efficiency of district heating networks.
This use case demonstrates the integration of various data sources and analytical tools within the InfDB ecosystem to derive meaningful metrics for urban energy infrastructure planning.

![alt text](liz-browser.png)

## Run Linear Heat Density
To run the complete linear heat density toolchain, use the following command:
```bash
uv run python3 tools/tools.py -p linear
```
The InfDB connects several tools to determine linear heat density by estimating heat demand at the building level and processing street segments suitable for district heating.

To see the outputs of executing the tool you may, for example, review the Postgres database. If you have default configuration, you can run the following:
```bash
$ docker ps  # To get the ID of the container
$ docker exec -it <container ID> bash  # Start a new shell session in the container
$ psql --username=infdb_user -W --dbname=infdb  # Executed inside the container where password is found in config
```
Once inside the Postgres database within the Docker container:
```sql
SELECT * FROM linear_heat_density.linear_heat_density LIMIT 10;
```

You can also use pgAdmin or any other database client to connect to the database using the credentials and port specified in the configuration.




