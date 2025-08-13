-- create touching neighborhood tables
DROP TABLE IF EXISTS temp_touching_neighbors;
CREATE TEMP TABLE temp_touching_neighbors AS
SELECT a.id         AS a_id,
       b.id         AS b_id,
       a.floor_area AS a_area,
       b.floor_area AS b_area
FROM {output_schema}.buildings a
         JOIN {output_schema}.buildings b ON
    a.id != b.id AND
    a.building_use = 'Residential' AND
    b.building_use = 'Residential' AND
    a.geom && b.geom AND -- check for bbox intersection
    ST_DWithin(a.geom, b.geom, 0.01);

-- also includes counts of 0
DROP TABLE IF EXISTS temp_touching_neighbor_counts;
CREATE TEMP TABLE temp_touching_neighbor_counts AS
SELECT b.id as id, count(b_id) as count
FROM {output_schema}.buildings b
         LEFT JOIN temp_touching_neighbors n ON b.id = n.a_id
GROUP BY b.id;
