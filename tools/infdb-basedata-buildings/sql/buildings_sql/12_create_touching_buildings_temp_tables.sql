-- Summary: Creates temporary tables identifying touching residential buildings.
-- It computes adjacency relationships and neighbor counts, which are essential
-- for classifying building types in subsequent steps.

-- create touching neighborhood tables by computing each pair once (a.id < b.id), then symmetrize with UNION ALL
DROP TABLE IF EXISTS temp_touching_neighbors;
CREATE TEMP TABLE temp_touching_neighbors AS
WITH pairs AS (
  SELECT a.id         AS a_id,
         b.id         AS b_id,
         a.floor_area AS a_area,
         b.floor_area AS b_area,
         a.gemeindeschluessel AS a_gemeindeschluessel,
         b.gemeindeschluessel AS b_gemeindeschluessel
  FROM temp_buildings a
       JOIN temp_buildings b ON
      a.id < b.id AND
      a.building_use = 'Residential' AND
      b.building_use = 'Residential' AND
      b.geom && ST_Expand(a.geom, 0.01) AND
      ST_DWithin(a.geom, b.geom, 0.01)
)
SELECT * FROM pairs
UNION ALL
SELECT b_id, a_id, b_area, a_area, b_gemeindeschluessel, a_gemeindeschluessel FROM pairs;

CREATE INDEX IF NOT EXISTS idx_temp_touching_neighbors_b_gemeindeschluessel ON temp_touching_neighbors (b_gemeindeschluessel);
CREATE INDEX IF NOT EXISTS idx_temp_touching_neighbors_a_id ON temp_touching_neighbors (a_id);
CREATE INDEX IF NOT EXISTS idx_temp_touching_neighbors_b_id ON temp_touching_neighbors (b_id);
-- also includes counts of 0
DROP TABLE IF EXISTS temp_touching_neighbor_counts;
CREATE TEMP TABLE temp_touching_neighbor_counts AS
SELECT b.id as id, count(b_id) as count
FROM temp_buildings b
         LEFT JOIN temp_touching_neighbors n ON b.id = n.a_id
GROUP BY b.id;

CREATE INDEX IF NOT EXISTS idx_temp_touching_neighbor_counts_id ON temp_touching_neighbor_counts (id);

-- Gather statistics for downstream operations to use indexes effectively
ANALYZE temp_touching_neighbors;
ANALYZE temp_touching_neighbor_counts;
