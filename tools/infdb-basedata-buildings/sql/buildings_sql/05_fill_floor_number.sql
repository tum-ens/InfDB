-- Summary: Estimates and populates the floor_number for buildings. It
-- prioritizes existing data from buildings_lod2, validating it against
-- building height. Missing values are derived using average floor heights
-- per building use or standard fallback values.

-- Create statistics on buildings to avoid nested loop join
ANALYZE temp_buildings;

-- Step 1: Use storeysAboveGround from LOD2 data where available and reasonable
-- Use temp table because original table is not indexed
DROP TABLE IF EXISTS temp_floor_number_data;
CREATE TEMP TABLE temp_floor_number_data AS
SELECT
    b.feature_id,
    b.height,
    l.storeysAboveGround AS validated_floors
    -- Calculate if the source floors make sense given the height
    -- Typical floor height should be between 2.5m and 5m
FROM temp_buildings b
LEFT JOIN {input_schema}.building_view l
       ON b.feature_id = l.feature_id
      AND l.gemeindeschluessel = '{ags}'
;
CREATE INDEX ON temp_floor_number_data (feature_id);
CREATE INDEX ON temp_floor_number_data (validated_floors);

DELETE FROM temp_floor_number_data
WHERE validated_floors = 0
   OR validated_floors IS NULL
    OR height  < 2.0 * validated_floors-- Too short per floor, suspicious
    OR height  > 6.0 * validated_floors; -- Too tall per floor, suspicious


UPDATE temp_buildings b
SET floor_number = fnd.validated_floors
FROM temp_floor_number_data fnd
WHERE b.feature_id = fnd.feature_id;

-- Step 2: Calculate average floor height per building use from validated data
-- This gives us reliable floor heights to use for estimation
WITH average_floor_height AS (
    SELECT
        building_use_id,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY (height / NULLIF(floor_number, 0))) as median_height_per_floor,
        COUNT(*) as sample_count
    FROM temp_buildings
    WHERE floor_number IS NOT NULL AND floor_number > 0
    GROUP BY building_use_id
)
UPDATE temp_buildings b
SET floor_number = GREATEST(ROUND(b.height / afh.median_height_per_floor), 1)
FROM average_floor_height afh
WHERE b.floor_number IS NULL
  AND b.building_use_id = afh.building_use_id
  AND afh.sample_count >= 5  -- Only use if we have enough samples
  AND afh.median_height_per_floor IS NOT NULL;

-- Step 3: For remaining buildings, use overall median floor height by building use
-- Residential: ~3.0m, Commercial: ~3.5m, Public: ~3.5m
UPDATE temp_buildings b
SET floor_number = GREATEST(
    ROUND(
        b.height /
        CASE
            WHEN b.building_use = 'Residential' THEN 3.0
            WHEN b.building_use IN ('Commercial', 'Public') THEN 3.5
            ELSE 3.0
        END
    ),
    1
)
WHERE b.floor_number IS NULL;

-- Step 4: Final fallback for any remaining buildings (use 3.2m average)
UPDATE temp_buildings
SET floor_number = GREATEST(ROUND(height / 3.2), 1)
WHERE floor_number IS NULL
  AND height IS NOT NULL;

-- Step 5: Set minimum of 1 floor for buildings without height data
UPDATE temp_buildings
SET floor_number = 1
WHERE floor_number IS NULL;

DROP TABLE IF EXISTS temp_floor_number_data;
