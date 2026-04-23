-- Summary: Identifies and classifies Terraced Houses (TH). It looks for attached
-- residential buildings with similar dimensions and specific neighbor counts,
-- graph-based clustering to label linear structures of similar buildings.

-- Identify buildings with medium floor area, 2-3 floors, 1-2 neighbors and a similar floor area to their neighbors (within 20%)
UPDATE temp_buildings
SET building_type = 'TH'
WHERE building_use = 'Residential'
  AND building_type IS NULL
    AND ((floor_area BETWEEN 70 AND 150 AND floor_number BETWEEN 2 AND 3 AND

        EXISTS (SELECT 1
                FROM temp_touching_neighbor_counts
                WHERE temp_touching_neighbor_counts.id = temp_buildings.id
                  AND count BETWEEN 1 AND 2) AND
        EXISTS (SELECT 1
                FROM temp_touching_neighbors
                WHERE temp_touching_neighbors.a_id = temp_buildings.id
                  AND ABS(temp_touching_neighbors.a_area - temp_touching_neighbors.b_area) /
                      GREATEST(temp_touching_neighbors.a_area, temp_touching_neighbors.b_area) < 0.2))
    );


-- -- Buildings adjacent to at least 2 THs with similar floor area become TH
-- -- Note: this part is can not be transformed to graph-based solution, due to the 2-neighbour condition
--
-- DO
-- $$
--     DECLARE
--         updated_count INTEGER := 1;
--     BEGIN
--         WHILE updated_count > 0
--             LOOP
--                 WITH candidates AS (SELECT DISTINCT n.a_id
--                                     FROM temp_touching_neighbors n
--                                              JOIN {output_schema}.buildings nb ON n.b_id = nb.id
--                                              JOIN {output_schema}.buildings b1 ON n.a_id = b1.id
--                                     WHERE nb.building_type = 'TH'
--                                       AND ABS(n.a_area - n.b_area) / GREATEST(n.a_area, n.b_area) < 0.25
--                                       AND b1.building_use = 'Residential'
--                                       AND b1.building_type IS NULL
--                                       AND b1.gemeindeschluessel = nb.gemeindeschluessel
--                                     GROUP BY n.a_id
--                                     HAVING COUNT(*) >= 2)
--                 UPDATE {output_schema}.buildings b
--                 SET building_type = 'TH'
--                 FROM candidates
--                 WHERE b.id = candidates.a_id;
--
--                 GET DIAGNOSTICS updated_count = ROW_COUNT;
--                 -- RAISE NOTICE 'Rule 3 iteration: % buildings updated', updated_count;
--             END LOOP;
--     END
-- $$;


-- Propagate building_type 'TH' to unclassified adjacent buildings with similar characteristics.

-- Create Vertex set of buildings which could be of type 'TH'
CREATE TEMP TABLE filtered_buildings AS (
    SELECT id, geom, floor_area, floor_number, height, gemeindeschluessel
    FROM temp_buildings
    WHERE building_use = 'Residential'
    AND (building_type = 'TH'
        OR( building_type IS NULL
            AND floor_area BETWEEN 70 AND 150
            AND floor_number BETWEEN 2 AND 3
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
        AND b1.floor_number = b2.floor_number
        AND b2.geom && ST_Expand(b1.geom, 0.01)
        AND ST_DWithin(b1.geom, b2.geom, 0.01)
        AND ABS(b1.floor_area - b2.floor_area) / GREATEST(b1.floor_area, b2.floor_area) < 0.2
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

-- find all neighbourhood components which already have building_type 'TH' from 1a and mark them as 'TH' too.
WITH seed_components AS (
  SELECT DISTINCT bc.component
  FROM building_components bc
  JOIN temp_buildings b
    ON b.id = bc.id
  WHERE b.building_type = 'TH'
)
UPDATE temp_buildings b
SET building_type = 'TH'
FROM building_components bc
JOIN seed_components sc
  ON sc.component = bc.component
WHERE b.id = bc.id;



-- release memory
DROP TABLE IF EXISTS filtered_buildings;
DROP TABLE IF EXISTS building_edges;
DROP TABLE IF EXISTS building_components;
