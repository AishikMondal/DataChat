# import json
# import re

# from planner import build_schema_context, extract_json_object, validate_plan


# FOLLOWUP_PATTERNS = [
#     r"^now\b",
#     r"^only\b",
#     r"^just\b",
#     r"^filter\b",
#     r"^make it\b",
#     r"^change\b",
#     r"^instead\b",
#     r"^sort\b",
#     r"^group\b",
#     r"^show only\b",
#     r"^for \d{4}\b",
#     r"\bonly for\b",
#     r"\bexclude\b",
#     r"\binclude\b",
# ]


# def is_followup_question(question):
#     q = question.strip().lower()
#     return any(re.search(pattern, q) for pattern in FOLLOWUP_PATTERNS)


# def refine_query_plan(question, previous_plan, model, table_name, column_types):
#     if model is None:
#         raise RuntimeError(
#             "Gemini API key not found. Set API_KEY as an environment variable or in .streamlit/secrets.toml"
#         )

#     schema_context = build_schema_context(column_types)
#     previous_plan_json = json.dumps(previous_plan, indent=2)

#     prompt = f"""
# You are updating an existing analytics query plan for a SQLite BI dashboard.

# Table name: {table_name}

# Available columns:
# {schema_context}

# Previous plan:
# {previous_plan_json}

# Return ONLY valid JSON with this exact structure:
# {{
#   "metric": "column_name_or_null",
#   "aggregation": "sum|avg|count|min|max|none",
#   "dimensions": ["column1", "column2"],
#   "filters": [
#     {{
#       "column": "column_name",
#       "operator": "=",
#       "value": "some_value"
#     }}
#   ],
#   "limit": 10,
#   "sort_by": "value_or_column_name_or_null",
#   "sort_order": "asc_or_desc",
#   "chart_type": "line|bar|table|pie",
#   "title": "short dashboard title"
# }}

# Rules:
# - Start from the previous plan and modify it according to the user's follow-up request.
# - Keep the previous metric, dimensions, and filters unless the user clearly changes them.
# - For phrases like "now only for 2023", add or replace a year filter.
# - For phrases like "sort ascending", update sort_order.
# - For phrases like "top 5", update limit.
# - Use ONLY the available columns.
# - Return JSON only.
# - No markdown.
# - No explanation.

# Follow-up request: {question}
# """

#     response = model.generate_content(prompt)
#     raw_plan = extract_json_object(response.text.strip())
#     return validate_plan(raw_plan, column_types)
import json
import re

from planner import build_schema_context, extract_json_object, validate_plan


FOLLOWUP_PATTERNS = [
    r"^now\b",
    r"^only\b",
    r"^just\b",
    r"^filter\b",
    r"^make it\b",
    r"^change\b",
    r"^instead\b",
    r"^sort\b",
    r"^group\b",
    r"^show only\b",
    r"^for \d{4}\b",
    r"\bonly for\b",
    r"\bexclude\b",
    r"\binclude\b",
]


def is_followup_question(question):
    q = question.strip().lower()
    return any(re.search(pattern, q) for pattern in FOLLOWUP_PATTERNS)


def refine_query_plan(question, previous_plan, model, table_name, column_types, schema_profile=None):
    if model is None:
        raise RuntimeError(
            "Gemini API key not found. Set API_KEY as an environment variable or in .streamlit/secrets.toml"
        )

    schema_context = build_schema_context(column_types=column_types, schema_profile=schema_profile)
    previous_plan_json = json.dumps(previous_plan, indent=2)

    prompt = f"""
You are updating an existing analytics query plan for a SQLite BI dashboard.

{schema_context}

Previous plan:
{previous_plan_json}

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
- Start from the previous plan and modify it according to the user's follow-up request.
- Keep the previous metric, dimensions, and filters unless the user clearly changes them.
- For phrases like "now only for 2023", add or replace a year filter.
- For phrases like "sort ascending", update sort_order.
- For phrases like "top 5", update limit.
- Use ONLY the available columns.
- Return JSON only.
- No markdown.
- No explanation.
- When the user asks for multiple values of the same column, use operator "IN" with a list of values.

Follow-up request: {question}
"""

    response = model.generate_content(prompt)
    raw_plan = extract_json_object(response.text.strip())
    return validate_plan(raw_plan, column_types)