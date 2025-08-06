DROP TABLE IF EXISTS {output_schema}.building_addresses;
CREATE TABLE IF NOT EXISTS {output_schema}.building_addresses AS
WITH split_addresses AS (
    SELECT b.id,
           a.city,
           a.country,
           a.street AS original_street,
           unnest(string_to_array(a.street, ';')) AS individual_street
    FROM {output_schema}.buildings b
             JOIN property p ON b.id = p.feature_id
             JOIN address a ON p.val_address_id = a.id
)
SELECT id as building_id,
       regexp_replace(trim(individual_street), '\s*\d+[\w,]*$', '') AS street,
       (regexp_match(trim(individual_street), '\s*(\d+[\w,]*)$'))[1] AS number,
       city,
       country,
       original_street
FROM split_addresses;

-- Add foreign key constraint after table creation
ALTER TABLE {output_schema}.building_addresses
ADD CONSTRAINT fk_building_addresses_building_id
FOREIGN KEY (building_id) REFERENCES {output_schema}.buildings(id);
