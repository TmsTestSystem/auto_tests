import os
import sys

def main() -> int:
    try:
        import psycopg2
    except ImportError:
        print("psycopg2 not installed", file=sys.stderr)
        return 2

    host = os.getenv("PGHOST", "localhost")
    port = int(os.getenv("PGPORT", "5432"))
    user = os.getenv("PGUSER", "postgres")
    password = os.getenv("PGPASSWORD", "postgres")
    database = os.getenv("PGDATABASE", "postgres")

    try:
        conn = psycopg2.connect(host=host, port=port, user=user, password=password, dbname=database)
        conn.autocommit = True
    except Exception as e:
        print(f"Connection failed: {e}")
        return 1

    try:
        with conn.cursor() as cur:
            cur.execute("SELECT current_database(), current_schema();")
            db, schema = cur.fetchone()
            print(f"Connected to DB={db}, schema={schema}")

            cur.execute("""
                SELECT table_schema, table_name
                FROM information_schema.tables
                WHERE table_schema NOT IN ('pg_catalog','information_schema')
                ORDER BY table_schema, table_name
            """)
            rows = cur.fetchall()
            if not rows:
                print("No user tables found.")
            else:
                print("Tables:")
                for sch, tbl in rows:
                    print(f"  {sch}.{tbl}")
    finally:
        conn.close()

    return 0

if __name__ == "__main__":
    raise SystemExit(main())



