-- ============================================================
-- Split intersecting ways in ways_tem at intersection points
--
-- Notes:
-- - Iterates over LINESTRING geometries in `ways_tem`
-- - Finds another LINESTRING that intersects the interior of the current way
-- - Computes an intersection point (midpoint of the buffered intersection segment)
-- - Deletes both original ways and reinserts split segments via {output_schema}.insert_way_segment
-- - Continues until all candidate intersections encountered in the scan are processed
-- ============================================================

DO $$
DECLARE
    -- Current way being processed (geometry, classification, AGS, id)
    way               RECORD;
    
    -- Calculated intersection point geometry container
    interpolate_point RECORD;
    
    -- Intersecting way selected for current way
    old_street        RECORD;
    
BEGIN
    -- Iterate through LINESTRING ways in the temporary table
    FOR way IN
        SELECT geom, klasse, ags, id
        FROM ways_tem
        WHERE ST_GeometryType(geom) = 'ST_LineString'  -- restrict to LINESTRING geometries
    LOOP
        -- Find one intersecting LINESTRING that intersects the interior of the current way
        -- ST_LineSubstring(0.01, 0.99) excludes endpoints to avoid endpoint-touch intersections
        SELECT geom, klasse, ags, id
        INTO old_street
        FROM ways_tem AS w
        WHERE ST_Intersects(ST_LineSubstring(way.geom, 0.01, 0.99), w.geom) 
            AND w.id != way.id  
            AND ST_GeometryType(w.geom) = 'ST_LineString'  -- restrict to LINESTRING geometries
        LIMIT 1;

        -- Skip if no intersecting way was found
        IF NOT FOUND THEN
            CONTINUE;
        END IF;

        -- Require the buffered intersection result to be a LINESTRING (needed for ST_LineInterpolatePoint)
        IF ST_Geometrytype(ST_Intersection(ST_Buffer(way.geom, 0.1), old_street.geom)) != 'ST_LineString' THEN
            CONTINUE;
        END IF;

        -- Compute intersection point: midpoint of the intersection LINESTRING
        SELECT ST_LineInterpolatePoint(ST_Intersection(ST_Buffer(way.geom, 0.1), old_street.geom), 0.5) AS geom
        INTO interpolate_point;

        -- Delete the original intersecting way row before inserting split segments
        DELETE
        FROM ways_tem
        WHERE id = old_street.id;

        -- Insert old_street split segment 1: start -> intersection point
        PERFORM {output_schema}.insert_way_segment(
            old_street.ags,    -- AGS tag for inserted segment
            old_street.klasse, -- preserve klasse of original way
            ST_LineSubstring(old_street.geom, 0, ST_LineLocatePoint(
                old_street.geom, interpolate_point.geom))
        );
        
        -- Insert old_street split segment 2: intersection point -> end
        PERFORM {output_schema}.insert_way_segment(
            old_street.ags,    -- AGS tag for inserted segment
            old_street.klasse, -- preserve klasse of original way
            ST_LineSubstring(old_street.geom, ST_LineLocatePoint(
                old_street.geom, interpolate_point.geom), 1)
        );

        -- Delete the original current way row before inserting split segments
        DELETE FROM ways_tem WHERE id = way.id;

        -- Insert current way split segment 1: start -> intersection point
        PERFORM {output_schema}.insert_way_segment(
            way.ags,    -- AGS tag for inserted segment
            way.klasse, -- preserve klasse of original way
            ST_LineSubstring(way.geom, 0, ST_LineLocatePoint(
                way.geom, interpolate_point.geom))
        );

        -- Insert current way split segment 2: intersection point -> end
        PERFORM {output_schema}.insert_way_segment(
            way.ags,    -- AGS tag for inserted segment
            way.klasse, -- preserve klasse of original way
            ST_LineSubstring(way.geom, ST_LineLocatePoint(
                way.geom, interpolate_point.geom), 1)
        );

    END LOOP; -- end scan over ways_tem
    
END;
$$;