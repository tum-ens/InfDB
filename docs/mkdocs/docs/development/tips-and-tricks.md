# For Developers

### Local development environment for InfDB for developers
```bash
# on linux and macos by installation script
curl -LsSf https://astral.sh/uv/install.sh | sh
# or by pip
pip install uv
```

### Git update with submodules
```bash
git submodule update --init --recursive
```

### Create environment (only once)
```bash
# linux and macos
uv sync
```

### Activate environment
```bash
# linux and macos
source .venv/bin/activate
# windows
venv\Scripts\activate
```
### Clean repo
```bash
git fetch origin
git reset --hard
git clean -fdx
```

### Stop and remove all docker containers and volumes
```bash
# 1. Stop all containers
docker stop $(docker ps -a -q)

# 2. Remove all containers (breaks the link to the volumes)
docker rm $(docker ps -a -q)

# 3. Delete all volumes
docker volume rm $(docker volume ls -q)
```

### Clean docker
```bash
docker system prune -a --volume
```

### Tree with permission
```bash
tree -pug
# -p permissions
# -u user
# -g group
```

### PyPi package build and upload
```bash
uv build
uv publish --token YOUR_PYPI_TOKEN
```

### PSQL Connection to InfDB
```bash
# on linux and macos
PGPASSWORD='citydb_password' psql -h localhost -p 5432 -U citydb_user -d citydb
```

### Configurations (only in addition for QGIS Desktop)
.pg_service.conf for QGIS to connect to InfDB via service
```
[infdb_postgres]
host=localhost
port=5432
dbname=citydb
user=citydb_user
password=citydb_password
sslmode=disable
```

### Git
```bash
# Check for uncommitted changes
git config --global pull.rebase true
git config --global rebase.autostash true
```

### pg_dump
Install pg_dump on Ubuntu:
```bash
# Install the common package
sudo apt-get update
sudo apt-get install -y postgresql-common

# Run the repository setup script (press Enter when prompted)
sudo /usr/share/postgresql-common/pgdg/apt.postgresql.org.sh
sudo apt-get update
sudo apt-get install -y postgresql-client-17

pg_dump --version
```

Run backup for schemas "basedata" and "linear_heat_density" in the "infdb" database, connecting to localhost on port 54328 with user "infdb_user", and output the backup in custom format to "infdb-nrw_backup.sql":
```bash
pg_dump -h localhost -p 54328 -U infdb_user -d infdb -n basedata -n linear_heat_density -F c > infdb-nrw_backup.sql
```