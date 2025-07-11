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
        WHEN 'Reitweg' THEN
            clazz := 92; kmh := 5;

        -- Rails
        WHEN 'Gleis' THEN
            clazz := 3; kmh := 50;
        WHEN 'Eisenbahn' THEN
            clazz := 3; kmh := 50;
        WHEN 'Zahnradbahn' THEN
            clazz := 3; kmh := 40;
        WHEN '["Eisenbahn", "S-Bahn"]' THEN
            clazz := 3; kmh := 50;

        -- Aerial transport
        WHEN 'Luftseilbahn, Großkabinenbahn' THEN
            clazz := 98; kmh := 30;
        WHEN 'Kabinenbahn, Umlaufseilbahn' THEN
            clazz := 98; kmh := 20;
        WHEN 'Sessellift' THEN
            clazz := 98; kmh := 15;
        WHEN 'Materialseilbahn' THEN
            clazz := 98; kmh := 10;

        -- Airfields
        WHEN 'Startbahn, Landebahn' THEN
            clazz := 99; kmh := 30;

        -- Special terrain
        WHEN 'Furt' THEN
            clazz := 99; kmh := 10;
        WHEN '(Kletter-)Steig im Gebirge' THEN
            clazz := 97; kmh := 3;

        -- Lifts
        WHEN 'Ski-, Schlepplift' THEN
            clazz := 96; kmh := 10;

        ELSE
            RAISE EXCEPTION 'Unknown way class: %', klasse;
    END CASE;
END;
$$ LANGUAGE plpgsql IMMUTABLE STRICT;
