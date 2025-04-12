CREATE TABLE bkg_grid_10km AS
SELECT
  row_number() OVER () AS id,
  ST_SetSRID(
    ST_MakePolygon(
      ST_MakeLine(ARRAY[
        ST_MakePoint(x, y),
        ST_MakePoint(x + 10000, y),
        ST_MakePoint(x + 10000, y + 10000),
        ST_MakePoint(x, y + 10000),
        ST_MakePoint(x, y)
      ])
    ), 3035
  ) AS geom
FROM generate_series(2500000, 4600000 - 10000, 10000) AS x, -- START, END, STEPSIZE
     generate_series(1400000, 3100000 - 10000, 10000) AS y; -- START, EBD, STEPSIZE


     --- Easting: 340000, Northing: 6600000) to (Easting: 1220000, Northing: 7800000