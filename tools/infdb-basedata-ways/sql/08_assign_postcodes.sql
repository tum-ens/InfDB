-- ============================================================
-- Populate postcode for ways_tem, ways_tem_connection, and connection_lines_tem using postcode polygons
--
-- Notes:
-- - Detects a target SRID once (from postcodes_germany.geom; falls back to {epsg} if SRID is 0/NULL)
-- - For each table, computes the intersection length between the road and each overlapping postcode
-- - Assigns the postcode where the greatest portion (length) of the road is located
-- - Transforms that point into the target SRID for consistent spatial predicates
-- - Joins against {input_schema}.postcodes_germany using bbox prefilter (&&) plus ST_Intersects
-- - Updates only rows with postcode IS NULL and valid, non-empty geometries
-- ============================================================

-- Precompute the target SRID once
DO $$
DECLARE
    v_srid integer; -- target SRID used for point transformation and intersection checks
BEGIN
    SELECT COALESCE(NULLIF(ST_SRID(geom), 0), {epsg}) -- use table SRID if set, else fallback to {epsg}
    INTO v_srid
    FROM {input_schema}.postcodes_germany
    WHERE geom IS NOT NULL AND NOT ST_IsEmpty(geom) -- require a valid polygon geometry
    LIMIT 1;

    -- Update ways_tem
    UPDATE ways_tem w
    SET postcode = final_pc.plz::int -- assign postcode as integer
    FROM (
        -- Select the postcode with the maximum intersection length for each road
        SELECT DISTINCT ON (rid) 
            rid, 
            plz
        FROM (
            SELECT
                w.ctid AS rid, -- row identifier used for stable join back to ways_tem
                pc.plz,
                ST_Length(ST_Intersection(ST_Transform(w.geom, v_srid), pc.geom)) AS intersect_len -- calculate length within polygon
            FROM ways_tem w
            JOIN {input_schema}.postcodes_germany pc
                ON pc.geom && ST_Transform(w.geom, v_srid) -- bbox prefilter for index usage
               AND ST_Intersects(pc.geom, ST_Transform(w.geom, v_srid)) -- spatial check
            WHERE w.postcode IS NULL
              AND w.geom IS NOT NULL
              AND NOT ST_IsEmpty(w.geom)
        ) AS lengths
        ORDER BY rid, intersect_len DESC -- ensure the longest segment's postcode is chosen
    ) final_pc
    WHERE w.ctid = final_pc.rid; -- update only the intended rows

    -- Update ways_tem_connection
    UPDATE ways_tem_connection w
    SET postcode = final_pc.plz::int -- assign postcode as integer
    FROM (
        -- Select the postcode with the maximum intersection length for each road
        SELECT DISTINCT ON (rid) 
            rid, 
            plz
        FROM (
            SELECT
                w.ctid AS rid, -- row identifier used for stable join back to ways_tem_connection
                pc.plz,
                ST_Length(ST_Intersection(ST_Transform(w.geom, v_srid), pc.geom)) AS intersect_len -- calculate length within polygon
            FROM ways_tem_connection w
            JOIN {input_schema}.postcodes_germany pc
                ON pc.geom && ST_Transform(w.geom, v_srid) -- bbox prefilter for index usage
               AND ST_Intersects(pc.geom, ST_Transform(w.geom, v_srid)) -- spatial check
            WHERE w.postcode IS NULL
              AND w.geom IS NOT NULL
              AND NOT ST_IsEmpty(w.geom)
        ) AS lengths
        ORDER BY rid, intersect_len DESC -- ensure the longest segment's postcode is chosen
    ) final_pc
    WHERE w.ctid = final_pc.rid; -- update only the intended rows

    -- Update connection_lines_tem from ways_tem
    UPDATE connection_lines_tem cl
    SET postcode = w.postcode -- copy postcode directly from the connected way
    FROM ways_tem w
    WHERE cl.postcode IS NULL
    AND cl.connected_way_id = w.id;

END;
$$;