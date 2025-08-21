from sqlalchemy.engine import Engine

def run_sql_script_pg(engine: Engine, path: str) -> None:
    """
    Execute a .sql file as-is using psycopg2 via SQLAlchemy's raw connection.
    Handles multi-statement scripts, functions, DO blocks, etc.
    """
    with open(path, "r", encoding="utf-8") as f:
        sql = f.read()

    # Optional: strip psql meta-commands (\...)
    lines = []
    for line in sql.splitlines():
        if line.lstrip().startswith("\\"):   # e.g., \echo, \connect, etc.
            continue
        lines.append(line)
    sql = "\n".join(lines)

    conn = engine.raw_connection()
    try:
        cur = conn.cursor()
        try:
            cur.execute(sql)
        finally:
            cur.close()
        conn.commit()
    finally:
        conn.close()
