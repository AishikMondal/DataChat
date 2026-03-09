import pandas as pd
import numpy as np


def format_value(value):
    if pd.isna(value):
        return "N/A"

    if isinstance(value, (int, float)):
        if abs(value) >= 1_000_000_000:
            return f"{value / 1_000_000_000:.2f}B"
        if abs(value) >= 1_000_000:
            return f"{value / 1_000_000:.2f}M"
        if abs(value) >= 1_000:
            return f"{value / 1_000:.2f}K"
        if float(value).is_integer():
            return f"{int(value):,}"
        return f"{value:,.2f}"

    return str(value)


def get_first_numeric_column(df, exclude=None):
    exclude = set(exclude or [])
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    for col in numeric_cols:
        if col not in exclude:
            return col
    return None


def get_first_categorical_column(df, exclude=None):
    exclude = set(exclude or [])
    for col in df.columns:
        if col not in exclude and df[col].dtype == "object":
            return col
    return None


def _detect_aggregation_type(plan):
    if not plan:
        return None
    agg = plan.get("aggregation", "none")
    if agg and agg != "none":
        return agg.upper()
    return None


def _is_ranking_query(plan):
    if not plan:
        return False
    return bool(plan.get("limit")) and plan.get("aggregation", "none") != "none"


def _detect_trend(df, numeric_col, time_col):
    if len(df) < 2:
        return None
    sorted_df = df.sort_values(time_col)
    first_val = sorted_df.iloc[0][numeric_col]
    last_val = sorted_df.iloc[-1][numeric_col]
    first_time = sorted_df.iloc[0][time_col]
    last_time = sorted_df.iloc[-1][time_col]

    if first_val == 0:
        pct = None
    else:
        pct = ((last_val - first_val) / abs(first_val)) * 100

    if last_val > first_val:
        direction = "increased"
    elif last_val < first_val:
        direction = "decreased"
    else:
        direction = "stayed flat"

    return {
        "direction": direction,
        "first_val": first_val,
        "last_val": last_val,
        "first_time": first_time,
        "last_time": last_time,
        "pct_change": pct,
    }


def generate_result_summary(df, plan):
    if df is None or df.empty:
        return "No rows were returned for this query."

    agg_type = _detect_aggregation_type(plan)

    # Single scalar result
    if len(df) == 1 and len(df.columns) == 1:
        value = df.iloc[0, 0]
        if pd.isna(value):
            return "The query returned no matching data. The filter may not match any rows — check the exact values in the dataset."
        label = agg_type or "Result"
        return f"{label}: {format_value(value)}."

    # Check if all numeric values are NaN (NULL from SQL)
    if len(df) == 1:
        import numpy as np
        numeric_cols_check = df.select_dtypes(include=np.number).columns.tolist()
        if numeric_cols_check and all(pd.isna(df.iloc[0][c]) for c in numeric_cols_check):
            return "The query returned NULL — no matching data found. The filter values may not match exactly. Check the dataset for correct spellings/values."

    if len(df) == 1:
        non_numeric_cols = [c for c in df.columns if df[c].dtype == "object"]
        numeric_col = get_first_numeric_column(df)

        if numeric_col:
            if non_numeric_cols:
                label = df.iloc[0][non_numeric_cols[0]]
                agg_label = f" ({agg_type})" if agg_type else ""
                return f"For {label}, {numeric_col}{agg_label} is {format_value(df.iloc[0][numeric_col])}."
            return f"The value is {format_value(df.iloc[0][numeric_col])}."

    # Time-series trend
    time_cols = [c for c in df.columns if c.lower() in {"year", "month", "date", "day", "quarter"}]
    datetime_cols = df.select_dtypes(include=["datetime"]).columns.tolist()
    time_col = datetime_cols[0] if datetime_cols else (time_cols[0] if time_cols else None)

    if time_col:
        numeric_col = get_first_numeric_column(df, exclude=[time_col])
        if numeric_col and len(df) >= 2:
            trend = _detect_trend(df, numeric_col, time_col)
            if trend:
                msg = (
                    f"{numeric_col} {trend['direction']} from {format_value(trend['first_val'])} "
                    f"in {trend['first_time']} to {format_value(trend['last_val'])} in {trend['last_time']}."
                )
                if trend["pct_change"] is not None:
                    msg += f" ({trend['pct_change']:+.1f}% change)"
                return msg

    # Ranking query
    if _is_ranking_query(plan):
        cat_col = get_first_categorical_column(df)
        numeric_col = get_first_numeric_column(df)
        if cat_col and numeric_col:
            top_row = df.iloc[0]
            limit = plan.get("limit", len(df))
            return (
                f"Top {limit} by {numeric_col} ({agg_type or 'value'}): "
                f"{top_row[cat_col]} leads with {format_value(top_row[numeric_col])}."
            )

    # Category vs numeric
    cat_col = get_first_categorical_column(df)
    numeric_col = get_first_numeric_column(df)

    if cat_col and numeric_col:
        sorted_df = df.sort_values(numeric_col, ascending=False)
        top_row = sorted_df.iloc[0]
        agg_label = f" ({agg_type})" if agg_type else ""
        return (
            f"{top_row[cat_col]} has the highest {numeric_col}{agg_label} "
            f"at {format_value(top_row[numeric_col])}."
        )

    return f"The query returned {len(df)} rows across {len(df.columns)} columns."


def generate_result_highlights(df, plan, max_items=8):
    if df is None or df.empty:
        return []

    highlights = []
    cat_col = get_first_categorical_column(df)
    numeric_col = get_first_numeric_column(df)
    agg_type = _detect_aggregation_type(plan)

    # Top / bottom contributor
    if cat_col and numeric_col and len(df) >= 2:
        sorted_df = df.sort_values(numeric_col, ascending=False)

        top_row = sorted_df.iloc[0]
        highlights.append(
            f"🥇 **Highest**: {top_row[cat_col]} → {format_value(top_row[numeric_col])}"
        )

        bottom_row = sorted_df.iloc[-1]
        highlights.append(
            f"🔻 **Lowest**: {bottom_row[cat_col]} → {format_value(bottom_row[numeric_col])}"
        )

    # Total
    if numeric_col:
        total = df[numeric_col].sum()
        highlights.append(f"📊 **Total** {numeric_col}: {format_value(total)}")

    # Average
    if numeric_col and len(df) >= 2:
        avg = df[numeric_col].mean()
        highlights.append(f"📏 **Average** {numeric_col}: {format_value(avg)}")

    # Median
    if numeric_col and len(df) >= 3:
        median = df[numeric_col].median()
        highlights.append(f"📐 **Median** {numeric_col}: {format_value(median)}")

    # Std deviation / spread
    if numeric_col and len(df) >= 3:
        std = df[numeric_col].std()
        avg = df[numeric_col].mean()
        if avg != 0:
            cv = (std / abs(avg)) * 100
            spread = "high variability" if cv > 50 else ("moderate spread" if cv > 20 else "tightly clustered")
            highlights.append(f"📉 **Spread**: {spread} (CV: {cv:.1f}%)")

    # Concentration: top contributor share
    if cat_col and numeric_col and len(df) >= 2:
        total = df[numeric_col].sum()
        if total > 0:
            sorted_df = df.sort_values(numeric_col, ascending=False)
            top_val = sorted_df.iloc[0][numeric_col]
            share = (top_val / total) * 100
            highlights.append(
                f"🏆 **Top share**: {sorted_df.iloc[0][cat_col]} accounts for {share:.1f}% of total"
            )
            # Top 3 combined share
            if len(df) >= 3:
                top3_val = sorted_df.iloc[:3][numeric_col].sum()
                top3_share = (top3_val / total) * 100
                top3_names = ", ".join(str(sorted_df.iloc[i][cat_col]) for i in range(min(3, len(df))))
                highlights.append(f"🔝 **Top 3** ({top3_names}) account for {top3_share:.1f}% combined")

    # Trend direction for time series
    time_cols = [c for c in df.columns if c.lower() in {"year", "month", "date", "day", "quarter"}]
    if time_cols:
        time_col = time_cols[0]
        nc = get_first_numeric_column(df, exclude=[time_col])
        if nc and len(df) >= 2:
            trend = _detect_trend(df, nc, time_col)
            if trend and trend["pct_change"] is not None:
                emoji = "📈" if trend["direction"] == "increased" else ("📉" if trend["direction"] == "decreased" else "➡️")
                highlights.append(f"{emoji} **Trend**: {trend['direction']} by {abs(trend['pct_change']):.1f}%")

    # Row count context
    if len(df) > 1:
        highlights.append(f"📋 **Rows returned**: {len(df)} across {len(df.columns)} columns")

    return highlights[:max_items]