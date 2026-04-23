SELECT regexp_replace(t.construction_data, '^.*_', '') AS building_type,
       t.element_name,
       t.construction_data,
       t.start_year,
       t.end_year,
       l.material_name,
       l.layer_index,
       l.thickness,
       m.thermal_conduc,
       m.heat_capac,
       m.density
FROM opendata.tabula_type_elements t
         JOIN opendata.tabula_layers l on l.element_id = t.element_id
         JOIN opendata.tabula_materials m on l.material_id = m.material_id
WHERE t.element_name != 'Door';