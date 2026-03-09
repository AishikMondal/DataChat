import os
import re
import sqlite3
from io import StringIO

import pandas as pd

from db_utils import DB_PATH, get_connection


def sanitize_name(name):
    name = os.path.splitext(name)[0].lower().strip()
    name = re.sub(r"[^a-z0-9]+", "_", name)
    name = re.sub(r"_+", "_", name).strip("_")

    if not name:
        name = "dataset"

    if name[0].isdigit():
        name = f"dataset_{name}"

    return name


def clean_column_name(col):
    col = str(col).strip().lower()
    col = re.sub(r"[^a-z0-9]+", "_", col)
    col = re.sub(r"_+", "_", col).strip("_")

    if not col:
        col = "column"

    if col[0].isdigit():
        col = f"col_{col}"

    return col


def clean_column_names(df):
    new_cols = []
    used = set()

    for col in df.columns:
        cleaned = clean_column_name(col)
        base = cleaned
        i = 1
        while cleaned in used:
            cleaned = f"{base}_{i}"
            i += 1
        used.add(cleaned)
        new_cols.append(cleaned)

    df.columns = new_cols
    return df


def read_uploaded_csv(uploaded_file):
    content = uploaded_file.getvalue().decode("utf-8", errors="ignore")
    df = pd.read_csv(StringIO(content))
    df = clean_column_names(df)
    return df


def ensure_unique_table_name(base_name, db_path=DB_PATH):
    existing = set(list_tables(db_path))
    if base_name not in existing:
        return base_name

    i = 1
    while f"{base_name}_{i}" in existing:
        i += 1

    return f"{base_name}_{i}"


def save_uploaded_csv(uploaded_file, db_path=DB_PATH):
    df = read_uploaded_csv(uploaded_file)
    base_table_name = sanitize_name(uploaded_file.name)
    table_name = ensure_unique_table_name(base_table_name, db_path)

    conn = get_connection(db_path)
    df.to_sql(table_name, conn, if_exists="replace", index=False)
    conn.close()

    return table_name, df


def list_tables(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    query = """
        SELECT name
        FROM sqlite_master
        WHERE type='table'
          AND name NOT LIKE 'sqlite_%'
        ORDER BY name
    """
    tables = pd.read_sql_query(query, conn)["name"].tolist()
    conn.close()
    return tables


def preview_table(table_name, limit=10, db_path=DB_PATH):
    conn = get_connection(db_path)
    df = pd.read_sql_query(f'SELECT * FROM "{table_name}" LIMIT {limit}', conn)
    conn.close()
    return df