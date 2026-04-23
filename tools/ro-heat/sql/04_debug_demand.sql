CREATE OR REPLACE VIEW {output_schema}.debug_demand AS
SELECT
    ahd."heating:demand[kWh]",
    ((ahd."heating:demand[kWh]") / (brs.floor_area * brs.floor_number)) AS "heating:demand_per_area[kWh/m²]",
    brc.resistance,
    brc.capacitance,
    brs.*,
    bbl.id,
    bbl.feature_id,
    bbl.height,
    bbl.building_use,
    bbl.building_use_id,
    bbl.occupants,
    bbl.households,
    bbl.postcode,
    bbl.address_street_id,
    bbl.street,
    bbl.house_number,
    bbl.gemeindeschluessel,
    bbl.centroid,
    bbl.geom
FROM {output_schema}.buildings_refurbished_status brs
JOIN {output_schema}.annual_heating_demand ahd ON brs.building_objectid = ahd.building_objectid
JOIN {output_schema}.buildings_rc brc ON brs.building_objectid = brc.building_objectid
JOIN basedata.buildings bbl ON brs.building_objectid = bbl.objectid;