-- Summary: Post-processes building type assignments to ensure consistency and
-- match census data. It assigns a default type to remaining buildings, corrects
-- likely errors, and rebalances the distribution of building types (AB, MFH,
-- TH, SFH) per grid cell to align with statistical targets.

-- Step 5: Set rest to AB
UPDATE temp_buildings b
SET building_type = 'AB'
WHERE b.building_use = 'Residential'
  AND b.building_type IS NULL;


-- fix wrong assignments
UPDATE temp_buildings b
SET building_type = 'SFH'
FROM temp_touching_neighbor_counts nc
WHERE b.id = nc.id
  AND building_type IN ('MFH', 'AB')
  AND households = 1
  AND nc.count = 0;

UPDATE temp_buildings b
SET building_type = 'TH'
FROM temp_touching_neighbor_counts nc
WHERE b.id = nc.id
  AND building_type IN ('MFH', 'AB')
  AND households = 1
  AND nc.count != 0;

UPDATE temp_buildings b
SET building_type = 'MFH'
FROM temp_touching_neighbor_counts nc
WHERE b.id = nc.id
  AND building_type IN ('SFH', 'TH')
  AND households BETWEEN 2 AND 4;

UPDATE temp_buildings b
SET building_type = 'AB'
FROM temp_touching_neighbor_counts nc
WHERE b.id = nc.id
  AND building_type IN ('SFH', 'TH')
  AND households >= 5;

-- Rebalance according to census data
-- This script rebalances residential building types according to reference data
-- This step is hierarchical. AB are adjusted first, then MFH, then TH, thereby automatically adjusting SFH

-- Create a mapping between building types and reference columns
-- AB (Apartment Buildings) = mfh_13undmehrwohnungen + mfh_7bis12wohnungen
-- MFH (Multi-Family Houses) = mfh_3bis6wohnungen + freist_zfh + zfh_dhh
-- TH (Terraced Houses) = efh_reihenhaus + zfh_reihenhaus
-- SFH (Single Family Houses) = freiefh + efh_dhh

-- Step 1: Assign grid id for later use
ALTER TABLE temp_buildings ADD COLUMN grid_id text;
UPDATE temp_buildings
SET grid_id = g.id
FROM temp_buildings_grid_{census_building_type_resolution} g
WHERE ST_Contains(g.geom, centroid);

-- Step 2: Calculate current counts and target counts per grid for adjusting MFH
DROP TABLE IF EXISTS temp_grid_current;
CREATE TABLE temp_grid_current AS
WITH grid_current AS (
    SELECT
        g.id as grid_id,
        COUNT(CASE WHEN b.building_type = 'AB' THEN 1 END) as current_ab,
        COUNT(CASE WHEN b.building_type = 'MFH' AND b.households > 1 THEN 1 END) as current_mfh_eligible,
        COUNT(*) as total_buildings
    FROM temp_buildings b
    JOIN temp_buildings_grid_{census_building_type_resolution} g ON ST_Contains(g.geom, b.centroid)
    WHERE b.building_use = 'Residential' AND g.id IS NOT NULL
    GROUP BY g.id
)
SELECT * FROM grid_current;

-- Census target counts per grid cell being compared against
DROP TABLE IF EXISTS temp_grid_target;
CREATE TABLE temp_grid_target AS (
    SELECT
        id as grid_id,
        -- Calculate target counts from reference data
            COALESCE(mfh_13undmehrwohnungen, 0)
          + COALESCE(mfh_7bis12wohnungen, 0) AS target_ab,

            COALESCE(mfh_3bis6wohnungen, 0)
          + COALESCE(freist_zfh, 0) AS target_mfh,

            COALESCE(efh_reihenhaus, 0)
          + COALESCE(zfh_reihenhaus, 0)
          + COALESCE(zfh_dhh, 0)
          + COALESCE(efh_dhh, 0) AS target_th,

            COALESCE(freiefh, 0) AS target_sfh,

            COALESCE(freiefh, 0)
          + COALESCE(efh_dhh, 0)
          + COALESCE(efh_reihenhaus, 0)
          + COALESCE(freist_zfh, 0)
          + COALESCE(zfh_dhh, 0)
          + COALESCE(zfh_reihenhaus, 0)
          + COALESCE(mfh_3bis6wohnungen, 0)
          + COALESCE(mfh_7bis12wohnungen, 0)
          + COALESCE(mfh_13undmehrwohnungen, 0) AS total_target
    FROM temp_buildings_grid_{census_building_type_resolution} g
    WHERE g.id IS NOT NULL
    AND EXISTS (
        SELECT 1
        FROM temp_buildings b
        WHERE b.grid_id = g.id
    )
);

-- Calculate needed adjustments for MFH
DROP TABLE IF EXISTS temp_grid_comparisonab;
CREATE TABLE temp_grid_comparisonab AS
WITH grid_comparison AS (
    SELECT
        gc.grid_id,
        gc.current_ab,
        gc.current_mfh_eligible,
        gc.total_buildings,
        gt.target_ab,
        gt.total_target,
--         -- Calculate needed adjustments (scaled to current total)
        CASE WHEN gt.total_target > 0 THEN
            ROUND(gt.target_ab * gc.total_buildings::numeric / gt.total_target) - gc.current_ab
        ELSE 0 END as ab_adjustment
    FROM temp_grid_current gc
    LEFT JOIN temp_grid_target gt ON gc.grid_id = gt.grid_id
)

SELECT * FROM grid_comparison;

-- -- Step 3: Create conversion plan from  AB to MFH, and from MFH and TH to AB based on adjustment numbers
DROP TABLE IF EXISTS temp_building_rankings;
CREATE TABLE temp_building_rankings AS
WITH ab_to_mfh AS (
    SELECT
        b.id,
        b.building_type,
        b.households,
        b.occupants,
        b.floor_area,
        b.height,
        gc.grid_id,
        gc.ab_adjustment,
        ROW_NUMBER() OVER (
            PARTITION BY gc.grid_id
            ORDER BY b.floor_area * b.height ASC
        ) AS ab_to_mfh_conversion_rank,
        NULL::int AS mfh_to_ab_conversion_rank,
        NULL::int AS th_to_ab_conversion_rank
    FROM temp_buildings b
    JOIN temp_buildings_grid_{census_building_type_resolution} g
      ON ST_Contains(g.geom, b.centroid)
    JOIN temp_grid_comparisonab gc
      ON g.id = gc.grid_id
    WHERE
        b.building_use = 'Residential'
        AND gc.total_target > 0
        AND gc.ab_adjustment < 0
        AND b.building_type = 'AB'
),

mfh_to_ab AS (
    SELECT
        b.id,
        b.building_type,
        b.households,
        b.occupants,
        b.floor_area,
        b.height,
        gc.grid_id,
        gc.ab_adjustment,
        NULL::int AS ab_to_mfh_conversion_rank,
        ROW_NUMBER() OVER (
            PARTITION BY gc.grid_id
            ORDER BY b.floor_area * b.height DESC
        ) AS mfh_to_ab_conversion_rank,
        NULL::int AS th_to_ab_conversion_rank
    FROM temp_buildings b
    JOIN temp_buildings_grid_{census_building_type_resolution} g
      ON ST_Contains(g.geom, b.centroid)
    JOIN temp_grid_comparisonab gc
      ON g.id = gc.grid_id
    WHERE
        b.building_use = 'Residential'
        AND b.households > 1
        AND gc.total_target > 0
        AND gc.ab_adjustment > 0
        AND b.building_type = 'MFH'
),
-- Ranks TH for AB conversion if MFH are not sufficient
th_to_ab AS (
    SELECT
        b.id,
        b.building_type,
        b.households,
        b.occupants,
        b.floor_area,
        b.height,
        gc.grid_id,
        gc.ab_adjustment,
        NULL::int AS ab_to_mfh_conversion_rank,
        NULL::int AS mfh_to_ab_conversion_rank,
        ROW_NUMBER() OVER (
            PARTITION BY gc.grid_id
            ORDER BY b.floor_area * b.height DESC
        ) AS th_to_ab_conversion_rank
    FROM temp_buildings b
    JOIN temp_buildings_grid_{census_building_type_resolution} g
      ON ST_Contains(g.geom, b.centroid)
    JOIN temp_grid_comparisonab gc
      ON g.id = gc.grid_id
    WHERE
        b.building_use = 'Residential'
        AND gc.total_target > 0
        AND gc.ab_adjustment > 0
        AND b.building_type = 'TH'
        AND gc.ab_adjustment >= gc.current_mfh_eligible
)

SELECT * FROM th_to_ab
Union ALL
SELECT * FROM ab_to_mfh
UNION ALL
SELECT * FROM mfh_to_ab;

-- -- Create the conversion decisions for AB table with a single join
DROP TABLE IF EXISTS temp_conversion_decisions;
CREATE TABLE temp_conversion_decisions AS (
    SELECT
        br.id,
        br.building_type as original_type,
        br.households,
        br.occupants,
        br.grid_id,
        -- Determine new building type based on conversion needs and rankings
        CASE
            -- Convert AB to MFH
            WHEN br.ab_adjustment < 0 AND (
               br.building_type = 'AB' AND br.ab_to_mfh_conversion_rank <= ABS(br.ab_adjustment))
            THEN 'MFH'
            -- Convert MFH and TH to AB
            WHEN br.ab_adjustment > 0 AND (
                (br.building_type = 'MFH' AND br.households > 1 AND br.mfh_to_ab_conversion_rank <= br.ab_adjustment)
                OR (br.building_type = 'TH' AND br.th_to_ab_conversion_rank <= br.ab_adjustment - gc.current_mfh_eligible)
                )THEN 'AB'
            ELSE br.building_type

        END as new_type,

        -- Calculate new household counts
        CASE
            -- AB conversions
            WHEN br.ab_adjustment < 0 AND (
                (br.building_type = 'AB' AND br.ab_to_mfh_conversion_rank <= ABS(br.ab_adjustment))
                ) THEN GREATEST(br.households, 2)
            WHEN br.ab_adjustment > 0 AND (
               (br.building_type = 'MFH' AND br.households > 1 AND br.mfh_to_ab_conversion_rank <= br.ab_adjustment) OR
                (br.building_type = 'TH' AND br.th_to_ab_conversion_rank < Greatest(0, br.ab_adjustment - gc.current_mfh_eligible))
                ) THEN GREATEST(br.households, 2)
            ELSE br.households
        END as new_households

    FROM temp_building_rankings br
    JOIN temp_grid_comparisonab gc ON br.grid_id = gc.grid_id
);


DROP TABLE IF EXISTS temp_conversion_plan;
CREATE TABLE temp_conversion_plan AS
(
    SELECT
        id,
        original_type,
        new_type,
        households,
        new_households,
        GREATEST(occupants, new_households, CASE WHEN new_type = 'AB' THEN 2 ELSE 1 END) as new_occupants
    FROM temp_conversion_decisions
    WHERE original_type != new_type
);

-- Step 4: Apply all conversions
UPDATE temp_buildings
SET
    building_type = cp.new_type,
    households = cp.new_households,
    occupants = cp.new_occupants
FROM temp_conversion_plan cp
WHERE temp_buildings.id = cp.id;

-- Repeat for MFH
DROP TABLE IF EXISTS temp_grid_current;
CREATE TABLE temp_grid_current AS
WITH grid_current AS (
    SELECT
        g.id as grid_id,
        COUNT(CASE WHEN b.building_type = 'MFH' THEN 1 END) as current_mfh,
        COUNT(CASE WHEN b.building_type = 'TH' THEN 1 END) as current_th,
        COUNT(*) as total_buildings
    FROM temp_buildings b
    JOIN temp_buildings_grid_{census_building_type_resolution} g ON ST_Contains(g.geom, b.centroid)
    WHERE b.building_use = 'Residential' AND g.id IS NOT NULL
    GROUP BY g.id
)
SELECT * FROM grid_current;

DROP TABLE IF EXISTS temp_grid_comparisonmfh;
CREATE TABLE temp_grid_comparisonmfh AS
WITH grid_comparison AS (
    SELECT
        gc.grid_id,
        gc.current_mfh,
        gc.current_th,
        gc.total_buildings,
        gt.target_mfh,
        gt.total_target,
        Case WHEN gt.total_target > 0 THEN
            ROUND(gt.target_mfh * gc.total_buildings::numeric / gt.total_target) - gc.current_mfh
        ELSE 0 END as mfh_adjustment
    FROM temp_grid_current gc
    LEFT JOIN temp_grid_target gt ON gc.grid_id = gt.grid_id
)
SELECT * FROM grid_comparison;

DROP TABLE IF EXISTS temp_building_rankings;
CREATE TABLE temp_building_rankings AS
WITH TH_to_MFH AS (
    SELECT
        b.id,
        b.building_type,
        b.households,
        b.occupants,
        b.floor_area,
        b.height,
        gc.grid_id,
        gc.mfh_adjustment,
        NULL::int AS SFH_to_MFH_conversion_rank,
        ROW_NUMBER() OVER (
            PARTITION BY gc.grid_id
            ORDER BY b.floor_area * b.height DESC
        ) AS TH_to_MFH_conversion_rank,
        NULL::int AS MFH_to_TH_conversion_rank
    FROM temp_buildings b
    JOIN temp_buildings_grid_{census_building_type_resolution} g
      ON ST_Contains(g.geom, b.centroid)
    JOIN temp_grid_comparisonmfh gc
      ON g.id = gc.grid_id
    WHERE b.building_use = 'Residential'
      AND gc.total_target > 0
      AND gc.mfh_adjustment > 0
      AND b.building_type = 'TH'
),
SFH_to_MFH AS (
    SELECT
        b.id,
        b.building_type,
        b.households,
        b.occupants,
        b.floor_area,
        b.height,
        gc.grid_id,
        gc.mfh_adjustment,
        ROW_NUMBER() OVER (
            PARTITION BY gc.grid_id
            ORDER BY b.floor_area * b.height DESC
        ) AS SFH_to_MFH_conversion_rank,
        NULL::int AS TH_to_MFH_conversion_rank,
        NULL::int AS MFH_to_TH_conversion_rank
    FROM temp_buildings b
    JOIN temp_buildings_grid_{census_building_type_resolution} g
      ON ST_Contains(g.geom, b.centroid)
    JOIN temp_grid_comparisonmfh gc
      ON g.id = gc.grid_id
    WHERE b.building_use = 'Residential'
      AND gc.total_target > 0
      AND gc.mfh_adjustment > 0
      AND b.building_type = 'SFH'
      AND gc.mfh_adjustment > gc.current_th
),
MFH_to_TH AS (
    SELECT
        b.id,
        b.building_type,
        b.households,
        b.occupants,
        b.floor_area,
        b.height,
        gc.grid_id,
        gc.mfh_adjustment,
        NULL::int AS SFH_to_MFH_conversion_rank,
        NULL::int AS TH_to_MFH_conversion_rank,
        ROW_NUMBER() OVER (
            PARTITION BY gc.grid_id
            ORDER BY b.floor_area * b.height ASC
        ) AS MFH_to_TH_conversion_rank
    FROM temp_buildings b
    JOIN temp_buildings_grid_{census_building_type_resolution} g
      ON ST_Contains(g.geom, b.centroid)
    JOIN temp_grid_comparisonmfh gc
      ON g.id = gc.grid_id
    WHERE b.building_use = 'Residential'
      AND gc.total_target > 0
      AND gc.mfh_adjustment < 0
      AND b.building_type = 'MFH'
      AND b.households <= 2
)
SELECT * FROM SFH_to_MFH
UNION ALL
SELECT * FROM TH_to_MFH
UNION ALL
SELECT * FROM MFH_to_TH;

DROP TABLE IF EXISTS temp_conversion_decisions;
CREATE TABLE temp_conversion_decisions AS (
    SELECT
        br.id,
        br.building_type as original_type,
        br.households,
        br.occupants,
        br.grid_id,
        -- Determine new building type based on conversion needs and rankings
        CASE
            -- Convert to MFH to TH
            WHEN br.mfh_adjustment < 0 AND (
                br.building_type = 'MFH' AND br.households <= 2 AND br.MFH_to_TH_conversion_rank <= ABS(br.mfh_adjustment)
            ) THEN 'TH'
            -- Convert TH and SFH to MFH
            WHEN br.mfh_adjustment > 0 AND (
                (br.building_type = 'TH' AND br.TH_to_MFH_conversion_rank <= br.mfh_adjustment) OR
                (br.building_type = 'SFH' AND br.SFH_to_MFH_conversion_rank <= Greatest(0, br.mfh_adjustment - gc.current_th))
            ) THEN 'MFH'
            ELSE br.building_type
        END as new_type,

        CASE
            WHEN br.mfh_adjustment > 0 AND (
                (br.building_type = 'TH' AND br.TH_to_MFH_conversion_rank <= br.mfh_adjustment) OR
                (br.building_type = 'SFH' AND br.SFH_to_MFH_conversion_rank <= Greatest(0, br.mfh_adjustment - gc.current_th))
            )  THEN GREATEST(br.households, 2)

            ELSE br.households
        END as new_households

    FROM temp_building_rankings br
    JOIN temp_grid_comparisonmfh gc ON br.grid_id = gc.grid_id
);

DROP TABLE IF EXISTS temp_conversion_plan;
CREATE TABLE temp_conversion_plan AS
(
    SELECT
        id,
        original_type,
        new_type,
        households,
        new_households,
        GREATEST(occupants, new_households, CASE WHEN new_type = 'AB' THEN 2 ELSE 1 END) as new_occupants
    FROM temp_conversion_decisions
    WHERE original_type != new_type
);

UPDATE temp_buildings
SET
    building_type = cp.new_type,
    households = cp.new_households,
    occupants = cp.new_occupants
FROM temp_conversion_plan cp
WHERE temp_buildings.id = cp.id;

-- Repeat for THs
DROP TABLE IF EXISTS temp_grid_current;
CREATE TABLE temp_grid_current AS
WITH grid_current AS (
    SELECT
        g.id as grid_id,
        COUNT(CASE WHEN b.building_type = 'TH' THEN 1 END) as current_th,
        COUNT(*) as total_buildings
    FROM temp_buildings b
    JOIN temp_buildings_grid_{census_building_type_resolution} g ON ST_Contains(g.geom, b.centroid)
    WHERE b.building_use = 'Residential' AND g.id IS NOT NULL
    GROUP BY g.id
)
SELECT * FROM grid_current;

DROP TABLE IF EXISTS temp_grid_comparisonth;
CREATE TABLE temp_grid_comparisonth AS
WITH grid_comparison AS (
    SELECT
        gc.grid_id,
        gc.current_th,
        gc.total_buildings,
        gt.target_th,
        gt.total_target,
        Case WHEN gt.total_target > 0 THEN
            ROUND(gt.target_th * gc.total_buildings::numeric / gt.total_target) - gc.current_th
        ELSE 0 END as th_adjustment
    FROM temp_grid_current gc
    LEFT JOIN temp_grid_target gt ON gc.grid_id = gt.grid_id
)

SELECT * FROM grid_comparison;

DROP TABLE IF EXISTS temp_building_rankings;
CREATE TABLE temp_building_rankings AS
WITH SFH_to_TH AS (
    SELECT
        b.id,
        b.building_type,
        b.households,
        b.occupants,
        b.floor_area,
        b.height,
        gc.grid_id,
        gc.th_adjustment,
        ROW_NUMBER() OVER (
            PARTITION BY gc.grid_id
            ORDER BY b.floor_area * b.height DESC
        ) AS SFH_to_TH_conversion_rank,
        NULL::int AS TH_to_SFH_conversion_rank
    FROM temp_buildings b
    JOIN temp_buildings_grid_{census_building_type_resolution} g
      ON ST_Contains(g.geom, b.centroid)
    JOIN temp_grid_comparisonth gc
      ON g.id = gc.grid_id
    WHERE b.building_use = 'Residential'
      AND gc.total_target > 0
      AND gc.th_adjustment > 0
      AND b.building_type = 'SFH'
),

TH_to_SFH AS (
    SELECT
        b.id,
        b.building_type,
        b.households,
        b.occupants,
        b.floor_area,
        b.height,
        gc.grid_id,
        gc.th_adjustment,
        NULL::int AS SFH_to_TH_conversion_rank,
        ROW_NUMBER() OVER (
            PARTITION BY gc.grid_id
            ORDER BY b.floor_area * b.height ASC
        ) AS TH_to_SFH_conversion_rank
    FROM temp_buildings b
    JOIN temp_buildings_grid_{census_building_type_resolution} g
      ON ST_Contains(g.geom, b.centroid)
    JOIN temp_grid_comparisonth gc
      ON g.id = gc.grid_id
    WHERE b.building_use = 'Residential'
      AND gc.total_target > 0
      AND gc.th_adjustment < 0
      AND b.building_type = 'TH'
)

SELECT * FROM SFH_to_TH
UNION ALL
SELECT * FROM TH_to_SFH;

DROP TABLE IF EXISTS temp_conversion_decisions;
CREATE TABLE temp_conversion_decisions AS (
    SELECT
        br.id,
        br.building_type as original_type,
        br.households,
        br.occupants,
        br.grid_id,
        CASE
            -- Convert to TH to SFH
            WHEN br.th_adjustment < 0 AND(
                br.building_type = 'TH' AND br.TH_to_SFH_conversion_rank <= ABS(br.th_adjustment))
            THEN 'SFH'
            -- Convert SFH to TH
            WHEN br.th_adjustment > 0 AND(
                br.building_type = 'SFH' AND br.SFH_to_TH_conversion_rank <= br.th_adjustment)
            THEN 'TH'
            ELSE br.building_type
        END as new_type,
        CASE
            WHEN br.th_adjustment < 0 AND (
                (br.building_type = 'TH' AND br.TH_to_SFH_conversion_rank <= ABS(br.th_adjustment))
                )
            THEN 1
            ELSE br.households
        END as new_households

    FROM temp_building_rankings br
    JOIN temp_grid_comparisonth gc ON br.grid_id = gc.grid_id
);

DROP TABLE IF EXISTS temp_conversion_plan;
CREATE TABLE temp_conversion_plan AS
(
    SELECT
        id,
        original_type,
        new_type,
        households,
        new_households,
        GREATEST(occupants, new_households, CASE WHEN new_type = 'AB' THEN 2 ELSE 1 END) as new_occupants
    FROM temp_conversion_decisions
    WHERE original_type != new_type
);

UPDATE temp_buildings
SET
    building_type = cp.new_type,
    households = cp.new_households,
    occupants = cp.new_occupants
FROM temp_conversion_plan cp
WHERE temp_buildings.id = cp.id;

ALTER TABLE temp_buildings DROP COLUMN IF EXISTS grid_id;

-- Drop TEMP tables
DROP TABLE IF EXISTS temp_grid_current;
DROP TABLE IF EXISTS temp_grid_target;
DROP TABLE IF EXISTS temp_grid_comparisonab;
DROP TABLE IF EXISTS temp_grid_comparisonmfh;
DROP TABLE IF EXISTS temp_grid_comparisonth;
DROP TABLE IF EXISTS temp_building_rankings;
DROP TABLE IF EXISTS temp_conversion_decisions;
DROP TABLE IF EXISTS temp_conversion_plan;
