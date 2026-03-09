import sqlite3
import pandas as pd

DB_PATH = "database.db"
DEFAULT_TABLE = "claims"


def get_connection(db_path=DB_PATH):
    return sqlite3.connect(db_path)


def get_schema_df(table_name=DEFAULT_TABLE, db_path=DB_PATH):
    conn = get_connection(db_path)
    schema_df = pd.read_sql_query(f'PRAGMA table_info("{table_name}")', conn)
    conn.close()
    return schema_df


def get_columns(table_name=DEFAULT_TABLE, db_path=DB_PATH):
    schema_df = get_schema_df(table_name, db_path)
    return schema_df["name"].tolist()


def get_column_types(table_name=DEFAULT_TABLE, db_path=DB_PATH):
    schema_df = get_schema_df(table_name, db_path)
    return dict(zip(schema_df["name"], schema_df["type"]))


def get_row_count(table_name=DEFAULT_TABLE, db_path=DB_PATH):
    conn = get_connection(db_path)
    row_count = pd.read_sql_query(
        f'SELECT COUNT(*) AS row_count FROM "{table_name}"', conn
    )["row_count"].iloc[0]
    conn.close()
    return int(row_count)


def run_query(sql, db_path=DB_PATH):
    conn = get_connection(db_path)
    df = pd.read_sql_query(sql, conn)
    conn.close()
    return df