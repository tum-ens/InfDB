-- ════════════════════════════════════════════════════════════════════════
-- CREATE LOCAL POSTCODE TABLE FOR GRID GENERATION
-- ════════════════════════════════════════════════════════════════════════
-- This script creates a table in the {output_schema} schema that contains
-- a simplified and renamed copy of the postcode geometries from 
-- {input_schema}."plz_plz-5stellig", transformed to SRID 3035.
-- ════════════════════════════════════════════════════════════════════════

-- 1. Drop the table if it already exists to allow clean recreation
DROP TABLE IF EXISTS {output_schema}.postcode;

-- 2. Create the new table with selected and renamed fields
CREATE TABLE {output_schema}.postcode AS
SELECT 
    plz,                                      -- 5-digit postal code
    note,                                     -- Optional annotation
    qkm,                                      -- Area in square kilometers
    einwohner AS population,                  -- Number of inhabitants
    ST_Transform(geometry, 3035) AS geom      -- Geometry transformed to EPSG:3035
FROM 
    {input_schema}."plz_plz-5stellig";

-- 3. Add a spatial index to improve performance for spatial queries
CREATE INDEX IF NOT EXISTS idx_postcode_geom 
    ON {output_schema}.postcode 
    USING GIST (geom);

-- 4. Add index on postcode for faster filtering/grouping
CREATE INDEX IF NOT EXISTS idx_postcode_code 
    ON {output_schema}.postcode (plz);
