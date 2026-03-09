from db_utils import get_row_count, get_schema_df, run_query


def quote_ident(name):
    return '"' + str(name).replace('"', '""') + '"'


def infer_column_role(column_name, data_type):
    name = str(column_name).lower()
    dtype = str(data_type).lower()

    if (
        name in {"year", "month", "day", "date"}
        or "date" in name
        or "time" in name
        or name.endswith("_at")
    ):
        return "time"

    if any(token in dtype for token in ["int", "real", "float", "double", "numeric", "decimal"]):
        return "numeric"

    if name.endswith("_amt") or name.endswith("_no") or name.endswith("_ratio"):
        return "numeric"

    return "categorical"


def get_distinct_sample_values(table_name, column_name, limit=5):
    try:
        sql = (
            f"SELECT DISTINCT {quote_ident(column_name)} AS value "
            f"FROM {quote_ident(table_name)} "
            f"WHERE {quote_ident(column_name)} IS NOT NULL "
            f"LIMIT {limit}"
        )
        df = run_query(sql)
        return [str(v) for v in df["value"].tolist()]
    except Exception:
        return []


def get_schema_profile(table_name, sample_limit=20):
    schema_df = get_schema_df(table_name)
    row_count = get_row_count(table_name)

    columns = []
    for _, row in schema_df.iterrows():
        column_name = row["name"]
        data_type = row["type"] if row["type"] else "UNKNOWN"
        role = infer_column_role(column_name, data_type)

        sample_values = []
        if role != "numeric":
            sample_values = get_distinct_sample_values(
                table_name=table_name,
                column_name=column_name,
                limit=sample_limit,
            )

        columns.append(
            {
                "name": column_name,
                "type": data_type,
                "role": role,
                "sample_values": sample_values,
            }
        )

    return {
        "table_name": table_name,
        "row_count": row_count,
        "columns": columns,
    }


def build_schema_context_from_profile(schema_profile):
    lines = [
        f"Table name: {schema_profile['table_name']}",
        f"Row count: {schema_profile['row_count']}",
        "Columns:",
    ]

    for col in schema_profile["columns"]:
        line = f"- {col['name']} ({col['type']}) [role: {col['role']}]"
        if col["sample_values"]:
            line += f" sample_values: {', '.join(col['sample_values'])}"
        lines.append(line)

    return "\n".join(lines)