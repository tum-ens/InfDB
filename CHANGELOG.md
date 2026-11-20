# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- `SECURITY.md` with private vulnerability reporting instructions
- `CHANGELOG.md` (this file)
- JOSS paper citation in `README.md`, `CITATION.cff` (`preferred-citation`), and the documentation
- `uv.lock` is committed for the root project (CI, tests) and `services/infdb-import`, so fresh installs and CI
  resolve the same dependency versions. CI runs `uv sync --locked` and fails when the lock file is out of date.
- infdb-import source `solarkataster-nrw`: rooftop PV potential per roof surface from the Solarkataster NRW
  (LANUK, dl-de/zero-2.0) for the NRW municipalities in scope, joinable to buildings via `objectid`.

### Fixed
- Fresh installs: pin SQLAlchemy `<2.1` and use the explicit `postgresql+psycopg2` driver.
  SQLAlchemy 2.1 defaults to psycopg (v3) and breaks `pandas.to_sql` in the bkg, osm, tabula and openmeteo loaders.

### Fixed
- PLZ import: the ArcGIS layer 0 download (`plz-5stellig`) was retired; the loader now uses layer 4
  (`PLZ_Gemeinde_Kreis`) and renames `postal_code` to `plz`. Layer 4 has no `einwohner`, `qkm` or `note`;
  these columns stay in `opendata.postcodes_germany` but are empty. Existing installations keep their own
  `configs/config-infdb-import.yml`: copy `url`, `filename` and `layer` of the `plz` source from the template.
- PLZ download: keeps the file only if it looks like a complete GeoJSON FeatureCollection (start and end are checked). ArcGIS Hub answers with a
  "Pending" status while it regenerates the export; that response was cached as the data file.

## [4.1.4] - 2026-06-09

- Release archived on Zenodo: https://doi.org/10.5281/zenodo.20609117
- Described in the JOSS paper: Buchenberg et al., (2026). InfDB: An Open Source Energy and Infrastructure Data Ecosystem for Modeling and Planning. *Journal of Open Source Software*, 11(122), 10458. https://doi.org/10.21105/joss.10458

For changes prior to this file's introduction, see the [commit history](https://github.com/tum-ens/InfDB/commits/).
