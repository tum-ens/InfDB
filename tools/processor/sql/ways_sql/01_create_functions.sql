/*
═══════════════════════════════════════════════════════════════════════════════
                    STREET CLASSIFICATION AND SPEED ASSIGNMENT FUNCTION
═══════════════════════════════════════════════════════════════════════════════

PURPOSE:
--------
This function maps German street classification names (Straße Klasse) to standardized 
numeric classification codes and typical speed limits. It provides consistent 
categorization of road networks for routing, analysis, and visualization purposes.

SPEED ASSIGNMENTS:
-----------------
Speed limits (kmh) represent typical maximum speeds for each road type:
- Based on osm data

INPUT/OUTPUT:
------------
INPUT:  klasse (TEXT) - German street classification name
OUTPUT: clazz (INTEGER) - Standardized numeric classification code
        kmh (INTEGER) - Typical speed limit in kilometers per hour

═══════════════════════════════════════════════════════════════════════════════
*/

CREATE OR REPLACE FUNCTION {output_schema}.map_strasse_klasse_to_class_kmh(
    klasse TEXT,
    OUT clazz INTEGER,
    OUT kmh INTEGER
)
AS $$
BEGIN
    CASE klasse
        -- MAIN ROADS (Federal Highway System)
        -- Highest capacity roads for long-distance travel
        WHEN 'Bundesautobahn' THEN
            clazz := 11; kmh := 120;    -- Federal Motorway
        WHEN 'Bundesstraße' THEN
            clazz := 13; kmh := 90;     -- Federal Road
        WHEN 'Landesstraße, Staatsstraße' THEN
            clazz := 15; kmh := 70;     -- State Road
        WHEN 'Kreisstraße' THEN
            clazz := 21; kmh := 60;     -- County/District Road
        
        -- LOCAL ROADS
        -- Municipal and community access roads
        WHEN 'Gemeindestraße' THEN
            clazz := 41; kmh := 40;     -- Municipal Road 
        WHEN 'Nicht öffentliche Straße' THEN
            clazz := 51; kmh := 5;      -- Private Road 

        -- AGRICULTURAL AND ECONOMIC WAYS
        -- Rural access roads for farming and forestry
        WHEN 'Wirtschaftsweg' THEN
            clazz := 71; kmh := 10;     -- Economic/Service Road
        WHEN 'Hauptwirtschaftsweg' THEN
            clazz := 71; kmh := 10;     -- Main Economic Road

        -- CYCLING INFRASTRUCTURE
        -- Dedicated bicycle transportation network
        WHEN 'Rad- und Fußweg' THEN
            clazz := 72; kmh := 10;     -- Combined Bike & Pedestrian Path
        WHEN 'Radweg ' THEN             
            clazz := 81; kmh := 10;     -- Dedicated Bicycle Path

        -- PEDESTRIAN INFRASTRUCTURE
        -- Foot traffic and walking paths
        WHEN 'Fußweg' THEN
            clazz := 91; kmh := 5;      -- Pedestrian Path/Sidewalk

        -- DEFAULT CASE
        -- Handles unknown or unmapped road types
        ELSE
            clazz := 99; kmh := 99;     -- Unknown/Unclassified 
    END CASE;
END;
$$ LANGUAGE plpgsql IMMUTABLE STRICT;