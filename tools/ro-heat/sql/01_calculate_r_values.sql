-- Calculation of r values according to DIN EN ISO 6946:2018-03
-- See table 7 for r_si and r_se values
-- Simplified consideration of thermal bridges, delta_U_WB = 0.1, according to DIN V 18599-2:2018-09, see section 6.2.5
WITH element_vars AS (SELECT 'OuterWall'::text  AS element_name,
                             'outer_wall'::text AS year_col,
                             'wall_area'::text  AS area_col,
                             0.13::numeric      AS r_si,
                             0.04::numeric      AS r_se,
                             0.1::numeric       AS delta_U_WB
                      UNION ALL
                      SELECT 'Rooftop', 'rooftop', 'roof_area', 0.10, 0.04, 0.1
                      UNION ALL
                      SELECT 'Window', 'window', 'window_area', 0.13, 0.04, 0.1
                      UNION ALL
                      SELECT 'GroundFloor', 'construction_year', 'floor_area', 0.17, 0.0, 0.1),
     element_data AS (SELECT b.building_id,
                             v.element_name,
                             vals.area_val::numeric              AS area,
                             -- R = d / lambda; see formula (3) in DIN EN ISO 6946:2018-03
                             -- sum (R_i); see formula (4) in DIN EN ISO 6946:2018-03
                             SUM(l.thickness / m.thermal_conduc) AS r_layers
                      FROM element_vars v
                               JOIN opendata.tba_type_elements t
                                    ON t.element_name = v.element_name
                               JOIN pylovo_input.buildings_rc b ON TRUE
                               JOIN LATERAL (
                          SELECT (to_jsonb(b) ->> v.year_col)::int     AS year_val,
                                 (to_jsonb(b) ->> v.area_col)::numeric AS area_val,
                                 CASE
                                     -- If the construction year matches year_col then lookup data in tabula_de_standard,
                                     -- else lookup data in tabula_de_retrofit
                                     WHEN (to_jsonb(b) ->> v.year_col)::int = b.construction_year
                                         THEN 'tabula_de_standard_1_' || b.building_type
                                     ELSE 'tabula_de_retrofit_1_' || b.building_type
                                     END                               AS construction_match
                          ) vals ON TRUE
                               JOIN opendata.tba_layers l
                                    ON t.element_id = l.element_id
                               JOIN opendata.tba_materials m
                                    ON l.material_id = m.material_id
                      WHERE vals.year_val BETWEEN t.start_year AND t.end_year
                        AND t.construction_data = vals.construction_match
                      GROUP BY b.building_id, v.element_name, vals.area_val),
     r_totals AS (SELECT e.building_id,
                         e.element_name,
                         e.area,
                         -- Calculate R_tot = R_Si + sum (R_i) + R_Se; see formula (4) in DIN EN ISO 6946:2018-03
                         -- Then calculate U = 1 / R_tot; see formula (1) in DIN EN ISO 6946:2018-03
                         -- Increase U by delta_U_WB to factor in thermal bridges; see section 6.2.5 in DIN V 18599-2:2018-09
                         -- Calculate H = U * A

                         -- H = U * A = (1 / (Rsi + sum(Ri) + Rse) + deltaU) * A
                         ((1 / (v.r_si + e.r_layers + v.r_se) + v.delta_U_WB) * e.area) AS h_value
                  FROM element_data e
                           JOIN element_vars v USING (element_name))
SELECT r.building_id,
       -- R = 1 / Ht´ = 1 / (sum(H) / sum(A))
       1 / (SUM(r.h_value) / NULLIF(SUM(r.area), 0)) AS r
FROM r_totals r
GROUP BY building_id
ORDER BY building_id;