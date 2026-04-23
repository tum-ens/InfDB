-- ============================================================
-- Merge ways_tem by chain_candidates
--
-- Notes:
-- - For each chain (array of way_ids), merges geometries into a single LINESTRING
-- - Inserts one new merged way row into `ways_tem`
-- - Deletes the original way rows that participated in the merge
-- - Preserves representative attributes (klasse/objektart/ags/postcode) from one member
-- - Uses snapping before union/linemerge to stabilize merges within a small tolerance
-- ============================================================

DROP TABLE IF EXISTS merged_ways_mapping;
CREATE TEMP TABLE merged_ways_mapping (
    old_way_id text NOT NULL,
    new_way_id text NOT NULL
);
CREATE INDEX ON merged_ways_mapping(old_way_id);

DO $$
DECLARE
    r RECORD; -- current chain row (chain_id, way_ids, way_count)
    v_new text; -- generated id for the merged way
    v_rows int; -- affected row count for INSERT verification

    -- Attributes chosen from one representative row (first id in chain)
    v_klasse text;     -- representative klasse
    v_objektart text;  -- representative objektart
    v_ags text;        -- representative AGS
    v_postcode integer; -- representative postcode

    v_geom geometry; -- merged geometry result
    v_distinct_ways text[]; -- distinct way ids in the chain
    v_snap_tol double precision := 0.25; -- snapping tolerance used during merge
BEGIN
    -- Iterate chains (largest first for determinism)
    FOR r IN
        SELECT chain_id, way_ids, way_count
        FROM chain_candidates
        ORDER BY way_count DESC, chain_id
    LOOP
        -- Skip empty / trivial chains
        IF r.way_ids IS NULL OR array_length(r.way_ids, 1) IS NULL OR array_length(r.way_ids, 1) < 2 THEN
            CONTINUE;
        END IF;

        -- Collect distinct way_ids to avoid processing duplicates
        SELECT array_agg(DISTINCT x) INTO v_distinct_ways
        FROM unnest(r.way_ids) AS x;

        -- Skip if only one distinct way remains
        IF v_distinct_ways IS NULL OR array_length(v_distinct_ways, 1) < 2 THEN
            CONTINUE;
        END IF;

        -- Generate a new id for the merged way
        v_new := md5(random()::text || clock_timestamp()::text);

        -- Pick representative attributes from the first way id in the chain
        SELECT w.klasse, w.objektart, w.ags, w.postcode
        INTO v_klasse, v_objektart, v_ags, v_postcode
        FROM ways_tem w
        WHERE w.id::text = v_distinct_ways[1] -- representative member
        LIMIT 1;

        -- Merge geometry for the whole chain with snapping tolerance
        WITH geom_collection AS (
            SELECT w.geom -- input geometries for this chain
            FROM ways_tem w
            WHERE w.id::text = ANY(v_distinct_ways)
        ),
        all_geoms AS (
            SELECT ST_Collect(geom) AS ref_geom -- reference geometry for snapping
            FROM geom_collection
        ),
        snapped_geoms AS (
            SELECT ST_Snap(g.geom, ag.ref_geom, v_snap_tol) AS geom -- snap each geom to the collection
            FROM geom_collection g
            CROSS JOIN all_geoms ag
        )
        SELECT ST_LineMerge(ST_Union(geom)) -- union then line-merge into a single linestring where possible
        INTO v_geom
        FROM snapped_geoms;

        -- Ensure result is always a LINESTRING (extract longest part if MULTILINESTRING)
        IF GeometryType(v_geom) = 'MULTILINESTRING' THEN
            SELECT part INTO v_geom
            FROM (
                SELECT (ST_Dump(v_geom)).geom AS part
            ) dumped
            ORDER BY ST_Length(part) DESC
            LIMIT 1;
        END IF;

        -- Skip if NULL/empty/not a linestring after extraction
        IF v_geom IS NULL OR ST_IsEmpty(v_geom) OR GeometryType(v_geom) <> 'LINESTRING' THEN
            RAISE WARNING 'Skipping chain % — could not extract valid LINESTRING', r.chain_id;
            CONTINUE;
        END IF;

        -- Insert merged way into ways_tem
        INSERT INTO ways_tem (id, klasse, objektart, geom, ags, postcode)
        VALUES (v_new, v_klasse, v_objektart, v_geom, v_ags, v_postcode);

        -- Record old->new mapping for building reassignment
        INSERT INTO merged_ways_mapping (old_way_id, new_way_id)
        SELECT unnest(v_distinct_ways), v_new;

        -- Delete original ways that were merged (distinct ids)
        DELETE FROM ways_tem
        WHERE id::text = ANY(v_distinct_ways);

        -- Insert-before-delete keeps the merged geometry present even if later steps fail
    END LOOP;

    PERFORM {output_schema}.update_assigned_way_id_after_merge('{ags}'); -- reassign building connections based on merged_ways_mapping
END $$;