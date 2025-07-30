# Setup Solar Potential Analysis
The instructions on how to use the tool can be found [here](https://advanced-gis-for-ee.netlify.app/software-lab-2/solar-potential-analysis)

```bash
docker login gitlab.lrz.de:5005 --username ge82buj --password glpat-mc1S_YrzT9XPJ-NgsVtu
docker pull gitlab.lrz.de:5005/sunpot/sunpot-core
```

The following parts are copied from the instructions above.
## Core Computations
```bash
docker run -i -t --rm --net=host --name sunpot-core \
  -v sunpotConfig.xml:/config/sunpotConfig.xml \
  gitlab.lrz.de:5005/sunpot/sunpot-core \
  -r -h localhost -p 1235 -d citydb -u postgres -pw need \
  /config/sunpotConfig.xml
```
## Texturing
```bash
docker run -i -t --net=host --name sunpot-tex \
 gitlab.lrz.de:5005/sunpot/sunpot-texture \
 -h localhost -p 1235 -d citydb -u postgres -pw need -y
```

## Migrating Solar Potential Calculations to CityDB v5 from CityDB v4
Currently solar potential calculations only run for CityDB v4.
Normally we load LOD2 data with `loaders` we have. You can check under `services/loader` directory for this.
We are using bind mounts, and once we download any file through `loader` we also have the data in the base project path.
So, in order to make Solar Potential Calculations, those LOD2 data is being inserted into CityDB v4 via Importer/Exporter tool.

Then Solarpotential calculations are executed and `sunpot` schema created.
At this step we run `export-and-import` service that has been developped under `src/services/sunpot`.
This service downloads data into csv, then loads those csvs to CityDB v5.

In order to test this, you have to be in the project base directory.
You should have CityDB v5 already running on your machine via `loader`.

Then you can run:
```bash
  docker-compose -f./dockers/sunpot/docker-compose.yml up --build
```

Services would run sequentially once CityDB v4 is ready.
