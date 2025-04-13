CREATE TABLE ali AS
SELECT
    '100kmN' || lpad((y / 100000)::text, 2, '0') || 'E' || lpad((x / 100000)::text, 2, '0') AS id,
  ST_SetSRID(
    ST_MakePolygon(
      ST_MakeLine(ARRAY[
        ST_MakePoint(x, y),
        ST_MakePoint(x + 100000, y),
        ST_MakePoint(x + 100000, y + 100000),
        ST_MakePoint(x, y + 100000),
        ST_MakePoint(x, y)
      ])
    ), 3035
  ) AS geom
FROM generate_series(4000000, 4600000, 100000) AS x, -- START, END, STEPSIZE
     generate_series(2600000, 3500000, 100000) AS y; -- START, EBD, STEPSIZE