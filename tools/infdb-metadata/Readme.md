# InfDB Dataschema-Knowledge-Graph (DKG) Generator

A containerized utility that inspects a PostgreSQL/PostGIS database and exports its schemas, tables, columns, and primary keys into [LinkML](https://linkml.io/)-shaped JSON and YAML. A Dataschema-Knowledge-Graph (DKG) is produced via `linkml-convert`.

# Table of Contents
- [Overview](#overview)
- [Workflow](#workflow)
- [Getting Started](#getting-started)
   - [Run the tool](#run-the-tool)
- [Project Structure](#project-structure)
   - [Keyfiles](#key-files)
- [Development Workflow](#development-workflow)
- [License and Citation](#license-and-citation)
- [Contact](#contact)


## Overview

This tool enables you to:
- Load DB connection details from `.env` and connect with `psycopg2`
- Enumerate non-system schemas, tables, and columns with primary keys
- Generate LinkML-shaped JSON/YAML plus optional TTL using `linkml-convert`
- Select schemas interactively or via `--schemas` CLI flag
- Run inside a VS Code dev container or Docker Compose service

## Workflow
DKG Generation flow:
1. Load environment variables from `.env` next to `compose.yml`.
2. Connect to PostgreSQL using `DB_URL` or `DB_HOST`/`DB_USER`/`DB_PASSWORD`/`DB_NAME`.
3. Collect schemas, tables, columns, and primary keys from `information_schema`.
4. Wrap metadata under the `Database` class defined in `src/schema.yaml`.
5. Write JSON/YAML to `OUTPUT_DIR` (defaults to `/app/mnt/data` in the container).
6. Attempt TTL generation with `linkml-convert` (skipped if the CLI is absent).

## Getting Started
### Run the tool

Prerequisites:
- [Docker Desktop](https://docs.docker.com/get-started/get-docker/) or Docker Engine
- A reachable PostgreSQL instance
- `.env` with DB credentials (see below)

**Option A — Docker Compose:**
```bash
docker compose -f tools/infdb-metadata/compose.yml up
```

**Option B — VS Code Dev Containers:**
1. Open `tools/infdb-metadata` in VS Code.
2. Install the “Dev Containers” extension.
3. Run “Dev Containers: Reopen in Container”.
4. Debug with F5; the container runs `main.py` which executes `src/infdb_metadata.py`.

If the container already exists and rebuilds fail:
```bash
docker compose -f tools/infdb-metadata/compose.yml down
```

## Project Structure

```
infdb-metadata/
├── src/                                 # Python source modules
│   ├── infdb_metadata.py                # Metadata extraction logic
│   └── schema.yaml                      # LinkML schema for serialization
├── configs/                             # Configuration files
│   └── config-infdb-metadata.yml        # Tool-specific config for InfDB wrapper
├── main.py                              # Entry point invoking metadata export
├── compose.yml                          # Docker Compose definition
├── Dockerfile                           # Container image build
├── pyproject.toml                       # Python dependencies (psycopg2, linkml)
└── mnt/data/                            # Mounted output folder (created at runtime)
```

### Key Files

#### `main.py`
Bootstraps the InfDB helper, then runs `src/infdb_metadata.py`. 

#### `src/infdb_metadata.py`
Core generator that:
- Parses `--schemas` (or prompts interactively) to filter schemas
- Connects with `psycopg2` using `.env` variables
- Writes LinkML-shaped JSON/YAML to `OUTPUT_DIR` (default `/app/mnt/data`)
- Attempts TTL generation with `linkml-convert` against `src/schema.yaml`

#### `src/schema.yaml`
LinkML model describing the `Database` class used for JSON/YAML/TTL serialization.

#### `compose.yml`
Defines the runtime container, mounts `./mnt` for outputs, and wires environment variables.

## Development Workflow
### Without infdb package
1. **Configure credentials**
   - Add a `.env` next to `compose.yml` with either `DB_URL` or `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`.
   - Optionally set `OUTPUT_DIR` to override `/app/mnt/data`.
   - Set `IRI_BASE` if you need a different base IRI for generated identifiers.

2. **Install dependencies**
   - Edit `pyproject.toml` if you add libraries, then run `uv sync` (locally) or rebuild the container.

3. **Run DKG generation**
   - `docker compose -f tools/infdb-metadata/compose.yml up`
   - Pass schema filters: `python src/infdb_metadata.py --schemas schema1 schema2` inside the container or via `docker compose ... --command`.

4. **Review outputs**
   - JSON/YAML saved under `/app/mnt/data` (mounted to `mnt/data` on the host).
   - TTL is created when `linkml-convert` is available; otherwise the script prints how to generate it manually.

### With infdb package
1. **Configure credentials**
With infdb package, you will configure the database connection in ./configs/config-infdb-metadata.yml file instead of in .env file.

2. **Same workflow as without infdb package**

## License and Citation

This tool is licensed under the **MIT License** (MIT).  
See [LICENSE](LICENSE) for rights and obligations.  
See the *Cite this repository* function or [CITATION.cff](CITATION.cff) for citation.

Copyright: [Institute of Energy Efficiency and Sustainable Building e3D, RWTH Aachen] | [MIT](LICENSE)

## Contact

Minsheng Xu  
Research Assosiate 
Institute of Energy Efficiency and Sustainable Building e3D, RWTH Aachen  
Email: xu@e3d.rwth-aachen.de

---

**Part of the infDB ecosystem**: [https://infdb.readthedocs.io/](https://infdb.readthedocs.io/)