def format_column_list(columns, max_items=10):
    if not columns:
        return ""

    preview = columns[:max_items]
    text = ", ".join(preview)

    if len(columns) > max_items:
        text += ", ..."
    return text


def format_user_error(error, active_table=None, columns=None):
    message = str(error)
    lowered = message.lower()

    if "gemini api key not found" in lowered:
        return (
            "API key not found. Set `API_KEY` as an environment variable "
            "or in `.streamlit/secrets.toml`."
        )

    if "planner could not return valid json" in lowered:
        return (
            "I could not clearly understand that dashboard request. "
            "Try being more specific about the metric and grouping."
        )

    if "unknown metric column" in lowered or "unknown dimension column" in lowered:
        base = "The query planner used a column that does not exist in the active dataset."
        if active_table:
            base += f" Active dataset: `{active_table}`."
        if columns:
            base += f" Available columns: {format_column_list(columns)}"
        return base

    if "i could not identify the column" in lowered:
        base = message
        if active_table:
            base += f" Active dataset: `{active_table}`."
        return base

    if "no such column" in lowered:
        base = "The requested column does not exist in the active dataset."
        if active_table:
            base += f" Active dataset: `{active_table}`."
        if columns:
            base += f" Available columns: {format_column_list(columns)}"
        return base

    if "only select queries are allowed" in lowered or "unsafe sql" in lowered:
        return "The generated query was blocked for safety. Please rephrase the request."

    if "no rows were returned" in lowered:
        return "The query ran successfully, but no matching rows were found."

    if "no such table" in lowered:
        return "The selected dataset could not be found. Re-select the active dataset and try again."

    return f"Request failed: {message}"