---
icon: material/play-circle
---
# Demo
Once InfDB has been successfully started and data has been imported, you can use the integrated tools or develop your own using the provided tool framework to interact with InfDB data. Detailed information on available tools and their usage is provided in the [Tools](https://tum-ens.github.io/InfDB/tools/) section of the documentation.

To run the Linear Heat Density demo, execute:
```bash
uv run python3 tools/tools.py -p linear
```
Additional information is available in the [Linear Heat Density](https://tum-ens.github.io/InfDB/linear-heat-density/) section of the documentation.

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