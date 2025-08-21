/*
═══════════════════════════════════════════════════════════════════════════════
                          WAY NAMES TABLE CREATION
═══════════════════════════════════════════════════════════════════════════════

PURPOSE:
--------
This script creates a `way_names` lookup table that maps internal way IDs
(from the routing-ready `ways` table) to their corresponding street names
from the basemap (`bmp_verkehrslinie`).

This is essential for:
- Matching building address strings to road segments

ALGORITHM OVERVIEW:
-------------------
1. Join routing table `ways` with raw data table `bmp_verkehrslinie` using
   the foreign key `verkehrslinie_id_basemap`
2. Extract both full name (`name`) and short name (`name_kurz`) for flexibility
3. Store the resulting mapping in a new `way_names` table

INPUT REQUIREMENTS:
-------------------
- {output_schema}.ways: Contains routing-ready road segments with internal way_id
- {input_schema}.bmp_verkehrslinie: Source street segments with name and name_kurz fields

OUTPUT:
-------
- {output_schema}.way_names table with the following columns:
    - way_id (int)
    - name (text)
    - name_kurz (text)
═══════════════════════════════════════════════════════════════════════════════
*/


CREATE TABLE IF NOT EXISTS {output_schema}.way_names AS
SELECT
    w.way_id AS way_id,
    v.name,
    v.name_kurz
FROM
    {output_schema}.ways w
JOIN
    {input_schema}.bmp_verkehrslinie v
ON
    w.verkehrslinie_id_basemap = v.id;
