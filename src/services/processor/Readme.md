# Process data

## Prequires
- Docker
- Have database set up with Open Data (see `src/services/loader`)

### Source Code
- The folder contains source code to create three tables in the `pylovo_input`:
  - `ways` (street segments)
  - `buildings` (buildings with 2D geometries and other data)
  - `way_names` (street names of ways)
  - `building_addresses` (addresses assigned to buildings)

### Startup
From the root project folder you can start the processor by executing these commands via bash:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements_processor.txt 

python3 -m src.services.processor.processor
```