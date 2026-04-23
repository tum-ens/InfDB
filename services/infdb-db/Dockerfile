FROM timescale/timescaledb-ha:pg17

# Install pgRouting + GDAL
USER root
RUN apt-get update && \
    apt-get install -y postgresql-17-pgrouting gdal-bin && \
    rm -rf /var/lib/apt/lists/*

# Copy 3DCityDB files and initialization script
COPY 3dcitydb-5.1.0 /tmp/3dcitydb
COPY 020_init-3dcitydb.sh /docker-entrypoint-initdb.d/020_init-3dcitydb.sh
RUN chmod +x /docker-entrypoint-initdb.d/020_init-3dcitydb.sh

# Docker volumes are owned by root but DB requires to own it by postgres user.
# Therefore, this init container sets the ownershop to postgres as root user before starting the real DB.
RUN mkdir -p /infdb-data && chown -R postgres:postgres /infdb-data

USER postgres