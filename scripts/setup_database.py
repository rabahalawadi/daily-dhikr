"""
Database setup script for Supabase PostgreSQL.
Applies schema, verifies tables, and seeds content.
"""
import os
import psycopg2

def setup_database(db_url: str):
    print("Connecting to Supabase PostgreSQL...")
    conn = psycopg2.connect(db_url)
    conn.autocommit = True
    cur = conn.cursor()

    print("Reading migrations/schema.sql...")
    with open("migrations/schema.sql", "r", encoding="utf-8") as f:
        schema_sql = f.read()

    print("Applying schema...")
    cur.execute(schema_sql)
    print("Schema applied successfully!")

    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        ORDER BY table_name;
    """)
    tables = [row[0] for row in cur.fetchall()]
    print("Public tables in database:", tables)

    conn.close()

if __name__ == "__main__":
    db_url = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres.soinkuylxddbturgdjss:478fMicdEewEfZYd@aws-0-ap-southeast-2.pooler.supabase.com:5432/postgres?sslmode=require"
    )
    setup_database(db_url)
