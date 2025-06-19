
# Changelog

All notable changes to this project will be documented in this file. 
See below for the format and guidelines for updating the changelog.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [Unreleased]
### Added
- Dockerized solar potential calculations on 3DCityDB v4 and migrated the workflow to 3DCityDB v5 using the Sunset service.
- Preconfigure PGAdmin in automatic startup (#78, !35)
- Developed a dynamic docker-compose generation flow to allow users to spin up local environments based on configuration. (#23, #25, #26, @27, !29)
- Automated geospatial data ingestion via CityDB v5 Loader service. (!29)
- Initialize CityDB v4 sunset (!27)
- Use single env file to share accros docker-compose files. (!25)
- Initial documentation of the repo (#21, !22)
- Implemented an API endpoint for retrieving historical weather data based on sensor names, matching with API specifications. Created raster table and integrated with automated weather data fetching. (#12, #13, !19)
- Set up initial CI pipeline steps, including dependency installation and lint checks. (!16, !17, !18)
- Creates initial docker file for deployment and requirement file (!12)
- Established the initial API structure, connecting TimescaleDB and 3DCityDB. (!7, !8, !9)

### Fixed
- Fix/ci resource size by updating artifact expiration date (#69, !34)
- Add healthchecks for databases in docker compose (!15)
- Convert post to get endpoint for citydb (!11)
- Get jupyter notebook volume path from config.yaml (#78, !35)

### Changed
- Optimize initial general config merge request !29 (!32)
- Fix/update db connection setup for data import (!24)
- Update raster table generation with a given lat and long in meters (#12, !21)
- add image build step to readme (!14)
- Update readme after initializing Imp/Exp (!13)
- Added comments on Imp/exp docker compose file and updated folder structure in the api (!11)

### Removed
- Cleanup unused queries and endpoints (#24, !20)

---

# Guidelines for Updating the Changelog
## [Version X.X.X] - YYYY-MM-DD
### Added
- Description of newly implemented features or functions, with a reference to the issue or MR number if applicable (e.g., `#42`).

### Changed
- Description of changes or improvements made to existing functionality, where relevant.

### Fixed
- Explanation of bugs or issues that have been resolved.
  
### Deprecated
- Note any features that are marked for future removal.

### Removed
- List of any deprecated features that have been fully removed.

---

## Example Entries

- **Added**: `Added feature to analyze time-series data from smart meters. Closes #10.`
- **Changed**: `Refined energy demand forecast model for better accuracy.`
- **Fixed**: `Resolved error in database connection handling in simulation module.`
- **Deprecated**: `Marked support for legacy data formats as deprecated.`
- **Removed**: `Removed deprecated API endpoints no longer in use.`

---

## Versioning Guidelines

This project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html):
- **Major** (X): Significant changes, likely with breaking compatibility.
- **Minor** (Y): New features that are backward-compatible.
- **Patch** (Z): Bug fixes and minor improvements.

**Example Versions**:
- **[2.1.0]** for a backward-compatible new feature.
- **[2.0.1]** for a minor fix that doesn’t break existing functionality.

## Best Practices

1. **One Entry per Change**: Each update, bug fix, or new feature should have its own entry.
2. **Be Concise**: Keep descriptions brief and informative.
3. **Link Issues or MRs**: Where possible, reference related issues or merge requests for easy tracking.
4. **Date Each Release**: Add the release date in `YYYY-MM-DD` format for each version.
5. **Organize Unreleased Changes**: Document ongoing changes under the `[Unreleased]` section, which can be merged into the next release version.

