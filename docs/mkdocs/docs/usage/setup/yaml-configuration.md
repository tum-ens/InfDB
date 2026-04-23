---
icon: material/file-code
---

# YAML Configuration

The configuration for the opendata import is done via a YAML file (default: `configs/config-infdb-import.yml`) due to its complexity.

For detailed configuration options of the **infdb-import**, refer to the [Services > infdb-import](../../infdb/services/infdb-import.md) documentation.

Below is an exemplary excerpt of the `config-infdb-import.yml` file:

```yaml title="configs/config-infdb-import.yml"
# Configuration file for infdb-import
#
# This configuration file contains tool-specific settings and database connection parameters.
#
# Database Connection Parameters:
# - Parameters set to 'None' will be automatically replaced with values from the central
#   configuration file specified in 'config-infdb' (config-infdb.yml by default)
# - This approach allows you to run locally using centralized database settings
# - To connect to a remote infdb instance, replace 'None' values with your specific
#   connection parameters (user, password, db, host, exposed_port, epsg)
#
infdb-import:
    name: "oberh_neub_sonth"  # Name of the infdb-import instance
    scope:  # AGS (Amtlicher Gemeindeschlüssel)
        # - "09162000"  # Munich
        - "09780139"  # Sonthofen
    multiproccesing: 
        status: not-active
        max_cores: 2    # max cores since of memory limitations to 2
    config-infdb: "config-infdb.yml" # only filename - change path in ".env" file "CONFIG_INFDB_PATH"
    path:
        opendata: "opendata/"
        processed: "{infdb-import/name}"
    logging:
        path: "infdb-import.log"
        level: "INFO" # ERROR, WARNING, INFO, DEBUG
    hosts:
        postgres:
            user: None
            password: None
            db: None
            host: None  # change to external IP if not running on local machine
            exposed_port: None
            epsg: None # 3035 (Europe)
        webdav:
            username: infdb
            access_token: "letdown subscribe lily catchable landmine sphinx"
    sources:
        # Service configuration examples...
        zensus_2022:
            status: active
            save_local: not-active
            datasets:
                - name: Bevoelkerungszahl
                  status: active
                  table_name: bevoelkerungszahl
                  year: 2022
                  url: https://www.destatis.de/static/DE/zensus/gitterdaten/Zensus2022_Bevoelkerungszahl.zip
```
###REVIEW: Fix nomenclature loader vs importer in all files to avoid confusion here?###
###REVIEW: I would suggest more generic region-independen names for the import docker...I dont see the advantage of changing this one every time parallel to the scopes, do you?###