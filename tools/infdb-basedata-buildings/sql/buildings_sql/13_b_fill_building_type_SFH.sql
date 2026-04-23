-- Summary: Identifies and classifies Single Family Houses (SFH). It targets
-- residential buildings with smaller dimensions and few neighbors, using
-- attribute filtering and graph-based clustering to assign the 'SFH' type.

-- Step 2: Single Family Houses (SFH):
-- Typically have larger floor area, 1-2 floors, and few or no neighbors
UPDATE temp_buildings
SET building_type = 'SFH'
WHERE building_use = 'Residential'
  AND building_type IS NULL
  AND ((floor_area < 350 AND floor_number <= 3 AND
        NOT EXISTS (SELECT 1
                    FROM temp_touching_neighbors
                    WHERE temp_touching_neighbors.a_id = temp_buildings.id)) OR
       (floor_area < 200 AND floor_number <= 2 AND
        NOT EXISTS (SELECT 1
                    FROM temp_touching_neighbor_counts
                    WHERE temp_touching_neighbor_counts.id = temp_buildings.id
                      AND count >= 2)));

-- Create Vertex set of buildings which could be of type 'SFH'
CREATE TEMP TABLE filtered_buildings AS (
    SELECT id, geom, height, gemeindeschluessel
    FROM temp_buildings
    WHERE
        building_use = 'Residential'
    AND (building_type = 'SFH'
        OR ( building_type IS NULL
            AND floor_area < 100
            AND floor_number <= 2
        )
    )
);

CREATE INDEX IF NOT EXISTS idx_filtered_buildings_geom ON filtered_buildings USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_filtered_buildings_id ON filtered_buildings(id);
CREATE INDEX IF NOT EXISTS idx_filtered_buildings_ags ON filtered_buildings(gemeindeschluessel);

-- edges in graph show neighbourhood relation with pre-computed neighbors from previous step
CREATE TEMP TABLE building_edges AS
SELECT ROW_NUMBER() OVER () AS id, n.a_id AS source, n.b_id AS target, 1.0 AS cost, 1.0 AS reverse_cost
FROM temp_touching_neighbors n
WHERE EXISTS (SELECT 1 FROM filtered_buildings fb WHERE fb.id = n.a_id)
  AND EXISTS (SELECT 1 FROM filtered_buildings fb WHERE fb.id = n.b_id);

CREATE INDEX IF NOT EXISTS building_edges_source_idx ON building_edges(source);
CREATE INDEX IF NOT EXISTS building_edges_target_idx ON building_edges(target);

-- Step 2: find connected components in graph which build a neighbourhood cluster
CREATE TEMP TABLE IF NOT EXISTS building_components AS
SELECT component,
       node AS id
FROM pgr_connectedComponents(
  'SELECT id, source, target, cost, reverse_cost FROM building_edges'::text
);

CREATE INDEX IF NOT EXISTS building_components_id_idx
    ON building_components(id);
CREATE INDEX IF NOT EXISTS building_components_component_idx
    ON building_components(component);

-- find all neighbourhood components which already have building_type 'SFH' and mark them as 'SFH' too.
WITH seed_components AS (
  SELECT DISTINCT bc.component
  FROM building_components bc
  JOIN temp_buildings b
    ON b.id = bc.id
  WHERE b.building_type = 'SFH'
)
UPDATE temp_buildings b
SET building_type = 'SFH'
FROM building_components bc
JOIN seed_components sc
  ON sc.component = bc.component
WHERE b.id = bc.id;

-- release memory
DROP TABLE IF EXISTS filtered_buildings;
DROP TABLE IF EXISTS building_edges;
DROP TABLE IF EXISTS building_components;
