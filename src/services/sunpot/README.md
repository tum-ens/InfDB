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