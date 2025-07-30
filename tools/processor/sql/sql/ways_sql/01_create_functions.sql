CREATE OR REPLACE FUNCTION pylovo_input.map_strasse_klasse_to_class_kmh(
    klasse TEXT,
    OUT clazz INTEGER,
    OUT kmh INTEGER
)
AS $$
BEGIN
    CASE klasse
        -- Main roads
        WHEN 'Bundesautobahn' THEN
            clazz := 11; kmh := 120;
        WHEN 'Bundesstraße' THEN
            clazz := 13; kmh := 90;
        WHEN 'Landesstraße, Staatsstraße' THEN
            clazz := 15; kmh := 70;
        WHEN 'Kreisstraße' THEN
            clazz := 21; kmh := 60;
        WHEN 'Gemeindestraße' THEN
            clazz := 41; kmh := 40;
        WHEN 'Nicht öffentliche Straße' THEN
            clazz := 51; kmh := 5;

        -- Paths and tracks
        WHEN 'Wirtschaftsweg' THEN
            clazz := 71; kmh := 10;
        WHEN 'Hauptwirtschaftsweg' THEN
            clazz := 71; kmh := 10;
        WHEN 'Rad- und Fußweg' THEN
            clazz := 72; kmh := 10;
        WHEN 'Fußweg' THEN
            clazz := 91; kmh := 5;
        WHEN 'Radweg ' THEN
            clazz := 81; kmh := 10;

        -- Default case for unknown types
        ELSE
            clazz := 99; kmh := 99;
    END CASE;
END;
$$ LANGUAGE plpgsql IMMUTABLE STRICT;
