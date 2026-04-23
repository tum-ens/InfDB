<p align="center">
   <img src="docs/img/logo_infdb_text.png" alt="Repo logo" width="250"/>
</p>

# infDB-loader - Open Data Importer

**The infDB-loader is an open source tool to import public opendata into infDB.**

| Category | Badges |
|----------|--------|
| License | [![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE) |
| Documentation | [![Documentation](https://img.shields.io/badge/docs-available-brightgreen)](https://gitlab.lrz.de/tum-ens/need/database) |
| Development | [![Open Issues](https://img.shields.io/badge/issues-open-blue)](https://gitlab.lrz.de/tum-ens/need/database/-/issues) [![Closed Issues](https://img.shields.io/badge/issues-closed-green)](https://gitlab.lrz.de/tum-ens/need/database/-/issues) [![Open MRs](https://img.shields.io/badge/merge_requests-open-blue)](https://gitlab.lrz.de/tum-ens/need/database/-/merge_requests) [![Closed MRs](https://img.shields.io/badge/merge_requests-closed-green)](https://gitlab.lrz.de/tum-ens/need/database/-/merge_requests) |
| Community | [![Contributing](https://img.shields.io/badge/contributions-welcome-brightgreen)](docs/contributing/CONTRIBUTING.md) [![Contributors](https://img.shields.io/badge/contributors-0-orange)](#) [![Repo Count](https://img.shields.io/badge/repo-count-brightgreen)](#) |

# How to register new data sources - for Developers
## Prepare Development Environment
1. Open `infdb-import` as folder in IDE
2. Make sure that no docker `infdb-import` exists on your machine (stop and/or remove if necessary)
3. Open folder in a VS Code devcontainer 
4. In `main.py`, comment the following lines for faster development:

5.  Comment lines 50-52 for development so that the schema is not dropped on every run: (faster and not need for development)
```
# Drop schema "opendata" for clean development runs
with infdb.connect() as db:  # InfdbClient context
      db.execute_query("DROP SCHEMA IF EXISTS opendata CASCADE;")
```
6. Comment all data sources loading processes which are not needed for your development to speed up the process (e.g., comment line 
`processes.append(mp.Process(target=need.load, args=(infdb,), name="need"))`)

## Register New Data Source
### Relevant files and folders:
- `main.py` is the main script to run the data loading process.
- `src/` contains scripts with load function for each data source.
- `configs/config-infdb-import.yml` contains all configuration parameters for the infDB-loader including which data sources to load.

### Registration process:
1. Create a new script in `src/` folder for your data source, e.g. `src/mydata.py`
2. Implement a `load(infdb: InfDB)` function in your script to load data from your data source into infDB. You can refer to existing scripts in the `src` folder for examples.
3. In `main.py`, import your new script at the top of the file:
```python
from src import mydata
```
4. In `main.py`, add a new process to the `processes` list to call your `load` function:
```python
processes.append(mp.Process(target=mydata.load, args=(infdb,), name="mydata"))
```
5. In `configs/config-infdb-import.yml`, add any necessary configuration needed to load your data.


## After development
1. Uncomment the lines you commented for development in `main.py`
2. Test your changes

# How to use bind-mount to load files directly into your host machine
## When to use
The current default setup creates a docker managed volume where all downloaded files are placed. 
The data in docker managed volume are persistent unless the volume is removed.
This default configuration allows to re-use downloaded files between runs of the infdb-import container,
but also a simple removal without enhanced user privilege.
Volume and therefore downloaded data can be removed for example by:
```bash
docker compose down -v
docker volume rm <volume_name>
docker volume prune
```
and similar commands. 
Also, as the volume management is done by the Docker engine, a de-installation or switch to other Docker engines can lead to loss of data in these volume.