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
