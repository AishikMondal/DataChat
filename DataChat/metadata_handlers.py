import re

from db_utils import (
    get_column_types,
    get_columns,
    get_row_count,
    get_schema_df,
    run_query,
)


def normalize_text(text):
    return re.sub(r"[^a-z0-9]+", " ", str(text).lower()).strip()


def humanize_column_name(column_name):
    text = column_name.lower()
    text = text.replace("_amt", " amount")
    text = text.replace("_no", " number")
    text = text.replace("_ratio", " ratio")
    text = text.replace("_", " ")
    return re.sub(r"\s+", " ", text).strip()


def match_column_from_question(question, columns):
    question_lower = question.lower()
    normalized_question = normalize_text(question)

    for column in sorted(columns, key=len, reverse=True):
        candidates = {
            column.lower(),
            column.lower().replace("_", " "),
            humanize_column_name(column),
        }
        for candidate in candidates:
            if candidate and candidate in question_lower:
                return column
            if candidate and candidate in normalized_question:
                return column

    return None


def extract_limit(question, default=10, max_limit=50):
    numbers = re.findall(r"\b(\d{1,3})\b", question)
    if numbers:
        return min(int(numbers[0]), max_limit)

    lowered = question.lower()
    if "few" in lowered:
        return 5
    if "all" in lowered:
        return max_limit
    return default


def classify_intent(question, columns):
    q = question.lower().strip()

    schema_keywords = [
        "dataset",
        "schema",
        "what columns",
        "which columns",
        "column names",
        "fields",
        "describe the data",
        "describe the dataset",
        "about the dataset",
        "what does this dataset contain",
        "table info",
        "metadata",
    ]
    if any(keyword in q for keyword in schema_keywords):
        return "schema"

    if ("datatype" in q or "data type" in q or "type of" in q) and match_column_from_question(question, columns):
        return "column_type"

    if ("unique" in q or "distinct count" in q or "how many distinct" in q) and match_column_from_question(question, columns):
        return "unique_count"

    if ("null" in q or "missing" in q or "blank" in q) and match_column_from_question(question, columns):
        return "null_count"

    if ("top" in q or "most frequent" in q or "most common" in q) and match_column_from_question(question, columns):
        return "top_values"

    sample_keywords = [
        "sample values",
        "example values",
        "distinct values",
        "sample entries",
        "example entries",
    ]
    if any(keyword in q for keyword in sample_keywords):
        return "sample_values"

    column_match = match_column_from_question(question, columns)
    value_request = bool(re.search(r"\b(show|give|tell|list|display)\b", q)) and "value" in q
    if value_request and column_match:
        return "sample_values"
    if ("sample" in q or "example" in q) and column_match:
        return "sample_values"

    return "dashboard"


def get_dataset_overview(table_name):
    schema_df = get_schema_df(table_name)[["name", "type"]].rename(
        columns={"name": "column_name", "type": "data_type"}
    )
    row_count = get_row_count(table_name)
    return row_count, schema_df


def get_sample_values(question, table_name):
    columns = get_columns(table_name)
    column_name = match_column_from_question(question, columns)

    if not column_name:
        raise ValueError(
            "I could not identify the column you want sample values for. "
            "Please mention one of these columns: " + ", ".join(columns)
        )

    limit = extract_limit(question)
    sql = (
        f'SELECT DISTINCT "{column_name}" '
        f'FROM "{table_name}" '
        f'WHERE "{column_name}" IS NOT NULL '
        f"LIMIT {limit}"
    )
    df = run_query(sql)
    return column_name, limit, sql, df


def get_column_datatype(question, table_name):
    columns = get_columns(table_name)
    column_name = match_column_from_question(question, columns)

    if not column_name:
        raise ValueError(
            "I could not identify the column name. Please mention one of these columns: "
            + ", ".join(columns)
        )

    column_types = get_column_types(table_name)
    return column_name, column_types.get(column_name, "UNKNOWN")


def get_unique_count(question, table_name):
    columns = get_columns(table_name)
    column_name = match_column_from_question(question, columns)

    if not column_name:
        raise ValueError(
            "I could not identify the column name. Please mention one of these columns: "
            + ", ".join(columns)
        )

    sql = f'SELECT COUNT(DISTINCT "{column_name}") AS unique_count FROM "{table_name}"'
    df = run_query(sql)
    return column_name, sql, int(df["unique_count"].iloc[0])


def get_null_count(question, table_name):
    columns = get_columns(table_name)
    column_name = match_column_from_question(question, columns)

    if not column_name:
        raise ValueError(
            "I could not identify the column name. Please mention one of these columns: "
            + ", ".join(columns)
        )

    sql = (
        f'SELECT COUNT(*) AS null_count '
        f'FROM "{table_name}" '
        f'WHERE "{column_name}" IS NULL'
    )
    df = run_query(sql)
    return column_name, sql, int(df["null_count"].iloc[0])


def get_top_values(question, table_name):
    columns = get_columns(table_name)
    column_name = match_column_from_question(question, columns)

    if not column_name:
        raise ValueError(
            "I could not identify the column name. Please mention one of these columns: "
            + ", ".join(columns)
        )

    limit = extract_limit(question, default=10, max_limit=25)
    sql = (
        f'SELECT "{column_name}", COUNT(*) AS frequency '
        f'FROM "{table_name}" '
        f'WHERE "{column_name}" IS NOT NULL '
        f'GROUP BY "{column_name}" '
        f"ORDER BY frequency DESC "
        f"LIMIT {limit}"
    )
    df = run_query(sql)
    return column_name, limit, sql, df