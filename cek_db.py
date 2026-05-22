import sqlite3
import pandas as pd
from config import DATABASE_PATH

print("DATABASE:", DATABASE_PATH)

conn = sqlite3.connect(DATABASE_PATH)

print("\n=== DAFTAR TABEL ===")
print(pd.read_sql("""
SELECT name
FROM sqlite_master
WHERE type='table';
""", conn))

print("\n=== WEEKLY SALES ===")

try:
    weekly = pd.read_sql("SELECT * FROM weekly_sales", conn)
    print(weekly)

except Exception as e:
    print("ERROR:", e)

conn.close()