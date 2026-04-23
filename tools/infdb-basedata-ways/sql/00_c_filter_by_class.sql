-- ============================================================
-- Apply optional filtering rules to remove rows from `ways_tem`
--
-- Notes:
-- - Filters are controlled by boolean flags:
--   - `{klasse_filter_enabled}` toggles class-based filtering via `{klasse_filter_tuple}`
--   - `{objektart_filter_enabled}` toggles objektart-based filtering for selected classes via
--     `{classes_with_obj_filter_tuple}` and `{objektart_filter_conditions}`
-- - A row is deleted if it matches either enabled filter block
-- ============================================================

DELETE FROM ways_tem
WHERE
  (
    ({klasse_filter_enabled}::boolean) AND klasse NOT IN {klasse_filter_tuple} -- delete when klasse-filter is enabled and klasse is not allowed
  )
  OR
  (
    ({objektart_filter_enabled}::boolean)                                      -- only apply objektart filter when enabled
    AND klasse IN {classes_with_obj_filter_tuple}                              -- only for classes that require objektart-based filtering
    AND NOT ( {objektart_filter_conditions} )                                  -- delete if none of the allowed objektart conditions match
  );