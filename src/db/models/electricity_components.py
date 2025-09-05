
def create_transformer_table(schema):
    sql = f"""
        CREATE TABLE {schema}.transformer (
        hv_bus INTEGER,
        lv_bus INTEGER,
        std_type TEXT,
        sn_mva DOUBLE PRECISION,
        vn_hv_kv DOUBLE PRECISION,
        vn_lv_kv DOUBLE PRECISION,
        vk_percent DOUBLE PRECISION,
        vkr_percent DOUBLE PRECISION,
        pfe_kw DOUBLE PRECISION,
        i0_percent DOUBLE PRECISION,
        shift_degree DOUBLE PRECISION,
        tap_side TEXT,
        tap_neutral INTEGER,
        tap_min INTEGER,
        tap_max INTEGER,
        tap_step_percent DOUBLE PRECISION,
        tap_step_degree DOUBLE PRECISION,
        tap_phase_shifter BOOLEAN
        ) INHERITS ({schema}.common_data);
    """
    utils.sql_query(sql)


def create_line_table(schema):
    sql = f"""
        CREATE TABLE {schema}.line (
            from_bus INTEGER,
            to_bus INTEGER,
            length_km DOUBLE PRECISION,
            geodata DOUBLE PRECISION[][],
            std_type TEXT,
            r_ohm_per_km DOUBLE PRECISION,
            x_ohm_per_km DOUBLE PRECISION,
            c_nf_per_km DOUBLE PRECISION,
            max_i_ka DOUBLE PRECISION,
            type TEXT,
            q_mm2 INTEGER,
            alpha DOUBLE PRECISION
        ) INHERITS ({schema}.common_data);
    """
    utils.sql_query(sql)


def create_switch_table(schema):
    sql = f"""
        CREATE TABLE {schema}.switch (
            bus INTEGER,
            element INTEGER,
            et TEXT,
            closed BOOLEAN,
            type INTEGER,
            name TEXT,
            z_ohm DOUBLE PRECISION,
            in_ka DOUBLE PRECISION
        ) INHERITS ({schema}.common_data);
    """
    utils.sql_query(sql)


def create_bus_table(schema):
    sql = f"""
        CREATE TABLE {schema}.bus (
            vn_kv INTEGER,
            geodata DOUBLE PRECISION[2],
            type TEXT,
            zone TEXT
        ) INHERITS ({schema}.common_data);
    """
    utils.sql_query(sql)

def electricity_network_components(schema):
    create_transformer_table(schema)
    create_line_table(schema)
    create_switch_table(schema)
    create_bus_table(schema)