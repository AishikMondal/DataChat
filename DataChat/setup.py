
# import pandas as pd
# import sqlite3

# df = pd.read_csv("data/sales.csv", encoding="latin1")

# conn = sqlite3.connect("database.db")
# df.to_sql("claims", conn, if_exists="replace", index=False)
# conn.close()

# print("Database created successfully")

import pandas as pd
import sqlite3

df = pd.read_csv("data/sales.csv", encoding="latin1")

df.columns = df.columns.str.strip()

# remove garbage rows
df = df[df["life_insurer"].notna()]
df = df[~df["life_insurer"].astype(str).str.contains("</html>|storage.googleapis.com|text/csv", case=False, na=False)]
df["life_insurer"] = df["life_insurer"].astype(str).str.strip()

conn = sqlite3.connect("database.db")
df.to_sql("claims", conn, if_exists="replace", index=False)
conn.close()

print(df.head())
print("Database created successfully")