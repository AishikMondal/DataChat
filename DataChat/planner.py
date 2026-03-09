import json
import re

from schema_utils import build_schema_context_from_profile


SUPPORTED_AGGREGATIONS = {"sum", "avg", "count", "min", "max", "none"}
SUPPORTED_CHART_TYPES = {"line", "bar", "table", "pie", "horizontal_bar", "grouped_bar", "scatter", "histogram"}
SUPPORTED_OPERATORS = {"=", "!=", ">", "<", ">=", "<=", "IN", "LIKE"}
SUPPORTED_SORT_ORDERS = {"asc", "desc"}


def build_schema_context(column_types=None, schema_profile=None):
    if schema_profile is not None:
        return build_schema_context_from_profile(schema_profile)

    column_types = column_types or {}
    lines = []
    for column, dtype in column_types.items():
        lines.append(f"- {column} ({dtype})")
    return "\n".join(lines)


def extract_json_object(text):
    cleaned = text.strip()
    cleaned = cleaned.replace("```json", "").replace("```", "").strip()

    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if not match:
        raise ValueError("Planner could not return valid JSON.")

    return json.loads(match.group(0))


def infer_chart_type(plan):
    dimensions = plan.get("dimensions", [])
    aggregation = plan.get("aggregation", "none")
    metric = plan.get("metric")

    if "year" in dimensions:
        return "line"

    if aggregation in {"sum", "avg", "count", "min", "max"} and len(dimensions) == 1:
        return "bar"

    if aggregation in {"sum", "avg", "count"} and len(dimensions) == 1:
        return "pie"

    if metric and not dimensions:
        return "table"

    return "table"


def validate_filters(filters, valid_columns):
    cleaned_filters = []

    for item in filters:
        if not isinstance(item, dict):
            continue

        column = item.get("column")
        operator = str(item.get("operator", "=")).upper()
        value = item.get("value")

        if column not in valid_columns:
            raise ValueError(f"Planner used an unknown filter column: {column}")

        if operator not in SUPPORTED_OPERATORS:
            raise ValueError(f"Unsupported filter operator: {operator}")

        cleaned_filters.append(
            {
                "column": column,
                "operator": operator,
                "value": value,
            }
        )

    return cleaned_filters


def validate_plan(raw_plan, column_types):
    valid_columns = set(column_types.keys())

    metric = raw_plan.get("metric")
    if metric is not None and metric not in valid_columns:
        raise ValueError(f"Planner used an unknown metric column: {metric}")

    aggregation = str(raw_plan.get("aggregation", "none")).lower()
    if aggregation not in SUPPORTED_AGGREGATIONS:
        aggregation = "none"

    dimensions = raw_plan.get("dimensions", [])
    if not isinstance(dimensions, list):
        dimensions = []

    cleaned_dimensions = []
    for dim in dimensions:
        if dim not in valid_columns:
            raise ValueError(f"Planner used an unknown dimension column: {dim}")
        if dim not in cleaned_dimensions:
            cleaned_dimensions.append(dim)

    filters = raw_plan.get("filters", [])
    if not isinstance(filters, list):
        filters = []
    cleaned_filters = validate_filters(filters, valid_columns)

    limit = raw_plan.get("limit")
    if limit is not None:
        try:
            limit = int(limit)
            limit = max(1, min(limit, 100))
        except Exception:
            limit = None

    sort_by = raw_plan.get("sort_by")
    allowed_sort_targets = set(cleaned_dimensions) | {"value", None}
    if metric:
        allowed_sort_targets.add(metric)

    if sort_by not in allowed_sort_targets:
        sort_by = None

    sort_order = str(raw_plan.get("sort_order", "desc")).lower()
    if sort_order not in SUPPORTED_SORT_ORDERS:
        sort_order = "desc"

    chart_type = str(raw_plan.get("chart_type", "")).lower()
    if chart_type not in SUPPORTED_CHART_TYPES:
        chart_type = infer_chart_type(
            {
                "dimensions": cleaned_dimensions,
                "aggregation": aggregation,
                "metric": metric,
            }
        )

    title = raw_plan.get("title")
    if not title:
        title = "Generated Dashboard"

    if metric is None and aggregation not in {"count", "none"}:
        aggregation = "none"

    if metric is None and not cleaned_dimensions and aggregation == "none":
        aggregation = "count"

    return {
        "metric": metric,
        "aggregation": aggregation,
        "dimensions": cleaned_dimensions,
        "filters": cleaned_filters,
        "limit": limit,
        "sort_by": sort_by,
        "sort_order": sort_order,
        "chart_type": chart_type,
        "title": title,
    }


def generate_query_plan(question, model, table_name, column_types, schema_profile=None):
    if model is None:
        raise RuntimeError(
            "Gemini API key not found. Set API_KEY as an environment variable or in .streamlit/secrets.toml"
        )

    schema_context = build_schema_context(column_types=column_types, schema_profile=schema_profile)

    prompt = f"""
You are planning an analytics query for a SQLite business intelligence app.

{schema_context}

Return ONLY valid JSON with this exact structure:
{{
  "metric": "column_name_or_null",
  "aggregation": "sum|avg|count|min|max|none",
  "dimensions": ["column1", "column2"],
  "filters": [
    {{
      "column": "column_name",
      "operator": "=",
      "value": "some_value"
    }}
  ],
  "limit": 10,
  "sort_by": "value_or_column_name_or_null",
  "sort_order": "asc_or_desc",
  "chart_type": "line|bar|table|pie",
  "title": "short dashboard title"
}}

Rules:
- Use ONLY the columns listed above.
- For filter values, use ONLY the exact sample_values shown above. Do NOT guess or expand abbreviations. If the user says "SBI", use the matching sample value exactly (e.g. "SBI Life" not "SBI Life Insurance").
- CRITICAL: Year/date values may be in special formats like "2021-22" or "FY2021". Always check the sample_values to use the correct format. If user says "2023", use LIKE operator with '%2023%' to match partial year strings, or find the exact sample value that contains "2023".
- Prefer one metric and up to two dimensions.
- For time trend questions, use year or a time-like column as a dimension and line as chart_type.
- For comparison questions, use bar.
- For count questions without a specific metric, set metric to null and aggregation to count.
- If no limit is needed, set limit to null.
- Do not include markdown.
- Do not include explanations.
- When the user asks for multiple values of the same column, use operator "IN".
- Do not emit multiple "=" filters for the same column unless they are truly separate impossible constraints.
- When the user asks for multiple values of the same column, use operator "IN" with a list of values.

Question: {question}
"""

    response = model.generate_content(prompt)
    raw_text = response.text.strip()
    raw_plan = extract_json_object(raw_text)
    return validate_plan(raw_plan, column_types)


def format_sql_value(value):
    if value is None:
        return "NULL"

    if isinstance(value, bool):
        return "1" if value else "0"

    if isinstance(value, (int, float)):
        return str(value)
    
    return "'" + str(value).replace("'", "''") + "'"

   
def build_filter_sql(node):
    if not node:
        return ""

    node_type = str(node.get("type", "")).upper()

    if node_type == "CONDITION":
        column = node["column"]
        operator = str(node["operator"]).upper()
        value = node["value"]

        if operator == "IN":
            if not isinstance(value, list) or not value:
                return ""
            values = ", ".join(format_sql_value(v) for v in value)
            return f'"{column}" IN ({values})'

        if operator == "LIKE":
            return f'"{column}" LIKE {format_sql_value(value)}'

        return f'"{column}" {operator} {format_sql_value(value)}'

    if node_type in {"AND", "OR"}:
        parts = []
        for child in node.get("children", []):
            child_sql = build_filter_sql(child)
            if child_sql:
                parts.append(child_sql)

        if not parts:
            return ""

        if len(parts) == 1:
            return parts[0]

        joiner = f" {node_type} "
        return "(" + joiner.join(parts) + ")"

    return ""



def dedupe_preserve_order(values):
    seen = set()
    result = []

    for value in values:
        key = repr(value)
        if key not in seen:
            seen.add(key)
            result.append(value)

    return result


def normalize_filters(filters):
    positive_by_column = {}
    negative_by_column = {}
    passthrough = []

    for item in filters:
        column = item["column"]
        operator = str(item["operator"]).upper()
        value = item["value"]

        if operator == "=" and isinstance(value, list):
            operator = "IN"

        if operator == "IN" and not isinstance(value, list):
            value = [value]

        if operator in {"=", "IN"}:
            values = value if operator == "IN" else [value]
            positive_by_column.setdefault(column, [])
            positive_by_column[column].extend(values)

        elif operator == "!=":
            negative_by_column.setdefault(column, [])
            negative_by_column[column].append(value)

        else:
            passthrough.append(
                {"column": column, "operator": operator, "value": value}
            )

    normalized = []

    for column, values in positive_by_column.items():
        values = dedupe_preserve_order(values)
        blocked = set(negative_by_column.get(column, []))
        values = [v for v in values if v not in blocked]

        if not values:
            return [], True

        if len(values) == 1:
            normalized.append(
                {"column": column, "operator": "=", "value": values[0]}
            )
        else:
            normalized.append(
                {"column": column, "operator": "IN", "value": values}
            )

    for column, values in negative_by_column.items():
        if column in positive_by_column:
            continue

        values = dedupe_preserve_order(values)
        for value in values:
            normalized.append(
                {"column": column, "operator": "!=", "value": value}
            )

    normalized.extend(passthrough)
    return normalized, False

def build_where_clause(filters):
    if not filters:
        return ""

    filters, impossible = normalize_filters(filters)
    if impossible:
        return " WHERE 1=0"

    conditions = []

    for item in filters:
        column = item["column"]
        operator = item["operator"]
        value = item["value"]

        if operator == "IN":
            if not isinstance(value, list) or not value:
                continue
            formatted_values = ", ".join(format_sql_value(v) for v in value)
            conditions.append(f'"{column}" IN ({formatted_values})')
        elif operator == "LIKE":
            conditions.append(f'"{column}" LIKE {format_sql_value(value)}')
        else:
            conditions.append(f'"{column}" {operator} {format_sql_value(value)}')

    if not conditions:
        return ""

    return " WHERE " + " AND ".join(conditions)




def build_sql_from_plan(plan, table_name):
    metric = plan["metric"]
    aggregation = plan["aggregation"]
    dimensions = plan["dimensions"]
    filters = plan["filters"]
    limit = plan["limit"]
    sort_by = plan["sort_by"]
    sort_order = plan["sort_order"]

    where_clause = build_where_clause(filters)
    quoted_table = f'"{table_name}"'

    raw_mode = aggregation == "none"

    if raw_mode and metric is None and dimensions:
        select_columns = ", ".join(f'"{col}"' for col in dimensions)
        sql = f"SELECT DISTINCT {select_columns} FROM {quoted_table}"
        sql += where_clause

        if "year" in dimensions:
            sql += ' ORDER BY "year" ASC'
        elif sort_by in dimensions:
            sql += f' ORDER BY "{sort_by}" {sort_order.upper()}'

        sql += f" LIMIT {limit or 50}"
        return sql

    select_parts = []
    group_by_parts = []

    for dim in dimensions:
        select_parts.append(f'"{dim}"')
        group_by_parts.append(f'"{dim}"')

    value_alias = "value"

    if aggregation == "count":
        select_parts.append(f"COUNT(*) AS {value_alias}")
    elif metric and aggregation == "none":
        select_parts.append(f'"{metric}"')
    elif metric:
        select_parts.append(f'{aggregation.upper()}("{metric}") AS {value_alias}')
    else:
        select_parts.append(f"COUNT(*) AS {value_alias}")

    sql = f"SELECT {', '.join(select_parts)} FROM {quoted_table}"
    sql += where_clause

    if group_by_parts and aggregation != "none":
        sql += " GROUP BY " + ", ".join(group_by_parts)

    if sort_by == "value" and (aggregation != "none" or metric is None):
        sql += f" ORDER BY {value_alias} {sort_order.upper()}"
    elif sort_by in dimensions:
        sql += f' ORDER BY "{sort_by}" {sort_order.upper()}'
    elif metric and sort_by == metric and aggregation == "none":
        sql += f' ORDER BY "{metric}" {sort_order.upper()}'
    elif "year" in dimensions:
        sql += ' ORDER BY "year" ASC'
    elif dimensions and aggregation != "none":
        sql += f" ORDER BY {value_alias} DESC"

    if limit is not None:
        sql += f" LIMIT {limit}"
    elif aggregation == "none":
        sql += " LIMIT 50"

    return sql


def summarize_plan(plan):
    metric = plan["metric"] or "row count"
    aggregation = plan["aggregation"]
    dimensions = plan["dimensions"]
    filters = plan["filters"]
    chart_type = plan["chart_type"]

    parts = [
        f"Metric: {metric}",
        f"Aggregation: {aggregation}",
        f"Chart: {chart_type}",
    ]

    if dimensions:
        parts.append("Dimensions: " + ", ".join(dimensions))

    if filters:
        filter_text = ", ".join(
            f'{f["column"]} {f["operator"]} {f["value"]}' for f in filters
        )
        parts.append("Filters: " + filter_text)

    return " | ".join(parts)