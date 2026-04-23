#!/bin/bash
# Script to initialize 3DCityDB in PostgreSQL
# This script runs automatically during container startup via docker-entrypoint-initdb.d

set -e

echo "======================================"
echo "Initializing 3DCityDB"
echo "======================================"

# Enable PostGIS extension
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE EXTENSION IF NOT EXISTS postgis;
EOSQL

# Set default values if not provided
SRID=${SRID:-4326}
HEIGHT_EPSG=${HEIGHT_EPSG:-0}
CHANGELOG=${CHANGELOG:-no}
SRS_NAME="urn:ogc:def:crs:EPSG::$SRID"

echo "Installing 3DCityDB with SRID=$SRID, HEIGHT_EPSG=$HEIGHT_EPSG, CHANGELOG=$CHANGELOG"

# Run the 3DCityDB creation script directly
# We bypass the shell script because it tries to connect via TCP/localhost which fails during init
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" \
    -f /tmp/3dcitydb/postgresql/sql-scripts/create-db.sql \
    -v srid="$SRID" \
    -v srs_name="$SRS_NAME" \
    -v changelog="$CHANGELOG"