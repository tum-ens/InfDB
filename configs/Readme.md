# Configs
We keep configurations under `configs/` folder in yaml format.

# Files
There is a central config.yaml that has a central configuration for whole InfDB.
Then currently there are two others `configs`
1. `config-services.yml`: Holds main service configuration (such as pgAdming, citydb)
2. `config-loader.yml`: Holds main loader configuration (volume mount paths, download urls etc)

If a service should be included during your tests, you should set `status: active`.

Both has some dependency over main `config.yml`. To solve this, while loading configuration, we merge those files together.
Then via the same config file, we provide methods like `config.get_value`, `config.get_value`.
For reference you can check under `src/services/loader/`.


Example:
```bash
    status = config.get_value(["loader", "basemap", "status"])
    citydb_db = config.get_value(["services", "citydb", "db"])
```
