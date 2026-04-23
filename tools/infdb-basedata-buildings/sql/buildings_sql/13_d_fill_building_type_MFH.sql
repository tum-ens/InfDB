-- Summary: Identifies and classifies Multi-Family Houses (MFH). It targets
-- medium-sized residential buildings that fall between single-family and
-- apartment buildings, using attribute criteria and graph-based analysis
-- to assign the 'MFH' type.

-- Step 4: Multi-Family Houses (MFH):
-- Buildings with 2-3 floors, multiple units but smaller than apartment buildings
-- Often have some neighbors but not as many as apartment buildings
UPDATE temp_buildings
SET building_type = 'MFH'
WHERE building_use = 'Residential'
  AND building_type IS NULL
  AND ((floor_number BETWEEN 2 AND 3 OR
        (floor_area > 150 AND
         EXISTS (SELECT 1
                 FROM temp_touching_neighbor_counts
                 WHERE temp_touching_neighbor_counts.id = temp_buildings.id
                   AND count BETWEEN 1 AND 3))
    ));

-- Create Vertex set of buildings which could be of type 'MFH'
CREATE TEMP TABLE filtered_buildings AS (
    SELECT id, geom, height, gemeindeschluessel
    FROM temp_buildings
    WHERE building_use = 'Residential'
    AND (building_type = 'MFH'
        OR( building_type IS NULL
    --AND floor_number BETWEEN 2 AND 3
        )
    )
)
;

CREATE INDEX IF NOT EXISTS idx_filtered_buildings_geom ON filtered_buildings USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_filtered_buildings_id ON filtered_buildings(id);
CREATE INDEX IF NOT EXISTS idx_filtered_buildings_ags ON filtered_buildings(gemeindeschluessel);

-- edges in graph show neighbourhood relation
CREATE TEMP TABLE building_edges(
    id SERIAL PRIMARY KEY,
    source INT,
    target INT,
    cost DOUBLE PRECISION,
    reverse_cost DOUBLE PRECISION
);
INSERT INTO building_edges(source, target, cost, reverse_cost)
SELECT  b1.id AS source,
        b2.id AS target,
        1.0   AS cost, -- undirected graph, therefore both direction are 1.0
        1.0   AS reverse_cost
FROM filtered_buildings b1
JOIN LATERAL (
    SELECT id
    FROM filtered_buildings b2
    WHERE b1.id < b2.id
      AND b1.gemeindeschluessel = b2.gemeindeschluessel
      AND b2.geom && ST_Expand(b1.geom, 0.01)
      AND ST_DWithin(b1.geom, b2.geom, 0.01)
) b2 ON true;

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

-- find all neighbourhood components which already have building_type 'MFH' from 1a and mark them as 'MFH' too.
WITH seed_components AS (
  SELECT DISTINCT bc.component
  FROM building_components bc
  JOIN temp_buildings b
    ON b.id = bc.id
  WHERE b.building_type = 'MFH'
)
UPDATE temp_buildings b
SET building_type = 'MFH'
FROM building_components bc
JOIN seed_components sc
  ON sc.component = bc.component
WHERE b.id = bc.id;

-- release memory
DROP TABLE IF EXISTS filtered_buildings;
DROP TABLE IF EXISTS building_edges;
DROP TABLE IF EXISTS building_components;
