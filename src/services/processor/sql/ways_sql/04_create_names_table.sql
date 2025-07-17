CREATE TABLE IF NOT EXISTS pylovo_input.way_names AS
SELECT
    w.way_id AS way_id,
    v.name,
    v.name_kurz
FROM
    pylovo_input.ways w
JOIN
    opendata.bmp_verkehrslinie v
ON
    w.verkehrslinie_id_basemap = v.id;
