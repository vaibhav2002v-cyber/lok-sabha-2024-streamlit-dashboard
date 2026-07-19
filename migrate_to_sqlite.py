"""
One-time migration script.

Run this ONCE on your own computer (where your local MySQL 'loksabha'
database is running) — NOT on Streamlit Cloud.

It copies every table your dashboard needs out of MySQL and into a
single SQLite file called loksabha.db. Once that file exists, commit
it to your GitHub repo alongside loksabha_app_live.py and you no
longer need a MySQL server at all — locally or in the cloud.
"""

import pandas as pd
from sqlalchemy import create_engine

# --- Your LOCAL MySQL connection ---
# (Change the password here to whatever you rotate it to.)
MYSQL_USER = "root"
MYSQL_PASSWORD = "CHANGE_ME"
MYSQL_HOST = "localhost"
MYSQL_PORT = "3306"
MYSQL_DB = "loksabha"

mysql_engine = create_engine(
    f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"
)

# --- Output SQLite file (created in the current folder) ---
sqlite_engine = create_engine("sqlite:///loksabha.db")

# Every table referenced anywhere in loksabha_app_live.py
TABLES = [
    "constituencywise_results",
    "constituencywise_details",
    "statewise_results",
    "partywise_results",
    "stats",
]

for table in TABLES:
    print(f"Exporting {table} ...")
    df = pd.read_sql(f"SELECT * FROM {table}", mysql_engine)
    df.to_sql(table, sqlite_engine, if_exists="replace", index=False)
    print(f"  -> {len(df)} rows written")

print("\nDone! loksabha.db has been created in this folder.")
print("Next steps:")
print("  1. Copy loksabha.db into your GitHub repo (same folder as loksabha_app_live.py)")
print("  2. git add loksabha.db")
print("  3. git commit -m 'Add SQLite database for cloud deployment'")
print("  4. git push")
