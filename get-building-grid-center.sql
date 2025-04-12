SELECT mapper.building_id, mapper.grid_id, ST_Centroid(g.geom) AS center
FROM test_building_grid_map mapper
JOIN test_grid g ON mapper.grid_id = g.id
--- following is an example value please adjust according to your needs
WHERE mapper.building_id = 42697