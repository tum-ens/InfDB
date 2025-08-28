CREATE OR REPLACE FUNCTION {output_schema}.classify_building_use(funktion TEXT)
    RETURNS TEXT AS
$$
BEGIN
    CASE funktion
        -- Residential Buildings
        WHEN '31001_1000' THEN RETURN 'Residential'; -- Wohngebäude
        WHEN '31001_2463' THEN RETURN 'Residential'; -- Garage
        WHEN '31001_9998' THEN RETURN 'Residential'; -- Unspecified

    -- Industrial Buildings
        WHEN '31001_2000' THEN RETURN 'Industrial'; -- Gebäude für Wirtschaft oder Gewerbe
        WHEN '31001_2513' THEN RETURN 'Industrial'; -- Wasserbehälter

    -- Commercial Buildings, stores and caffes
        WHEN '31001_2072' THEN RETURN 'Commercial'; -- Jugendherberge
        WHEN '31001_2461' THEN RETURN 'Commercial'; -- Parkhaus
        WHEN '31001_2465' THEN RETURN 'Commercial'; -- Tiefgarage
        WHEN '31001_3290' THEN RETURN 'Commercial'; -- Touristisches Informationszentrum

    -- Public Buildings, buildings by governments
        WHEN '31001_3091' THEN RETURN 'Public'; -- Bahnhofsgebäude
        WHEN '31001_3000' THEN RETURN 'Public'; -- Gebäude für öffentliche Zwecke
        WHEN '31001_3012' THEN RETURN 'Public'; -- Rathaus
        WHEN '31001_3017' THEN RETURN 'Public'; -- Kreisverwaltung
        WHEN '31001_3018' THEN RETURN 'Public'; -- Bezirksregierung
        WHEN '31001_3020' THEN RETURN 'Public'; -- Gebäude für Bildung und Forschung
        WHEN '31001_3031' THEN RETURN 'Public'; -- Schloss
        WHEN '31001_3038' THEN RETURN 'Public'; -- Burg, Festung
        WHEN '31001_3041' THEN RETURN 'Public'; -- Kirche
        WHEN '31001_3042' THEN RETURN 'Public'; -- Synagoge
        WHEN '31001_3043' THEN RETURN 'Public'; -- Kapelle
        WHEN '31001_3046' THEN RETURN 'Public'; -- Moschee
        WHEN '31001_3047' THEN RETURN 'Public'; -- Tempel
        WHEN '31001_3048' THEN RETURN 'Public'; -- Kloster
        WHEN '31001_3051' THEN RETURN 'Public'; -- Krankenhaus
        WHEN '31001_3052' THEN RETURN 'Public'; -- Heilanstalt, Pflegeanstalt, Pflegestation
        WHEN '31001_3065' THEN RETURN 'Public'; -- Kinderkrippe, Kindergarten, Kindertagesstätte
        WHEN '31001_3071' THEN RETURN 'Public'; -- Polizei
        WHEN '31001_3072' THEN RETURN 'Public'; -- Feuerwehr
        WHEN '31001_3073' THEN RETURN 'Public'; -- Kaserne
        WHEN '31001_3075' THEN RETURN 'Public'; -- Justizvollzugsanstalt
        WHEN '31001_3242' THEN RETURN 'Public'; -- Sanatorium

    -- Transformer Positions
        WHEN '31001_2523' THEN RETURN 'Transformer'; -- Umformer (Transformer & Wechselsrichter)

    -- Infrastructure or Misc (not classified, so raise error)
    --WHEN '31001_9998' THEN RAISE EXCEPTION 'Unspecified building type: %', funktion;
        WHEN '51007_1500' THEN RAISE EXCEPTION 'Structure (historical wall) is not a building: %', funktion;
        WHEN '51007_1800' THEN RAISE EXCEPTION 'Structure (wall) is not a building: %', funktion;
        WHEN '51009_1610' THEN RAISE EXCEPTION 'Structure (roofing) is not a building: %', funktion;
        WHEN '53001_1800' THEN RAISE EXCEPTION 'Structure (bridge) is not a building: %', funktion;
        WHEN '53009_2030' THEN RAISE EXCEPTION 'Structure (dam) is not a building: %', funktion;
        WHEN '53009_2050' THEN RAISE EXCEPTION 'Structure (weir) is not a building: %', funktion;

        ELSE RAISE EXCEPTION 'Unknown building function code: %', funktion;
        END CASE;
END;
$$ LANGUAGE plpgsql IMMUTABLE
                    STRICT;

CREATE OR REPLACE FUNCTION {output_schema}.assign_weighted_year(
    vor1919 double precision,
    a1919bis1948 double precision,
    a1949bis1978 double precision,
    a1979bis1990 double precision,
    a1991bis2000 double precision,
    a2001bis2010 double precision,
    a2011bis2019 double precision,
    a2020undspaeter double precision,
    r double precision
) RETURNS TEXT AS $$
DECLARE
    total NUMERIC;
BEGIN
    total := vor1919 + a1919bis1948 + a1949bis1978 + a1979bis1990 + a1991bis2000 + a2001bis2010 + a2011bis2019 + a2020undspaeter;

    IF total <= 0 THEN
        RETURN NULL;
    END IF;

    IF r < vor1919 / total THEN
        RETURN '-1919';
    ELSIF r < (vor1919 + a1919bis1948) / total THEN
        RETURN '1919-1948';
    ELSIF r < (vor1919 + a1919bis1948 + a1949bis1978) / total THEN
        RETURN '1949-1978';
    ELSIF r < (vor1919 + a1919bis1948 + a1949bis1978 + a1979bis1990) / total THEN
        RETURN '1979-1990';
    ELSIF r < (vor1919 + a1919bis1948 + a1949bis1978 + a1979bis1990 + a1991bis2000) / total THEN
        RETURN '1991-2000';
    ELSIF r < (vor1919 + a1919bis1948 + a1949bis1978 + a1979bis1990 + a1991bis2000 + a2001bis2010) / total THEN
        RETURN '2001-2010';
    ELSIF r < (vor1919 + a1919bis1948 + a1949bis1978 + a1979bis1990 + a1991bis2000 + a2001bis2010 + a2011bis2019) / total THEN
        RETURN '2011-2019';
    ELSE
        RETURN '2020-';
    END IF;
END;
$$ LANGUAGE plpgsql;