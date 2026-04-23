import sqlite3
from pathlib import Path

base_dir = Path(__file__).resolve().parent
db_path = base_dir / "database.db"
schema_path = base_dir / "schema.sql"

conn = sqlite3.connect(db_path)

with open(schema_path, "r", encoding="utf-8") as f:
    conn.executescript(f.read())

conn.commit()
conn.close()

print("Database created successfully.")