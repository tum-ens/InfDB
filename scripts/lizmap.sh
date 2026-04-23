git clone https://github.com/3liz/lizmap-docker-compose.git
cd lizmap-docker-compose
./configure.sh configure

docker compose pull
LIZMAP_PORT=0.0.0.0:8090 docker compose up

# scp -J need@need.energy:8081 infdb_validation\ 3.*  need@infdb-bynrw-dev:lizmap-docker-compose/lizmap/instances/infdb