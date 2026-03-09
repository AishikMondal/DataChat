import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


def determine_chart_type(df, plan=None):
    if df is None or df.empty:
        return "table"

    cols = df.columns.tolist()
    n_cols = len(cols)

    numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
    categorical_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
    datetime_cols = df.select_dtypes(include=["datetime"]).columns.tolist()

    # Check plan for SQL aggregation hints
    aggregation = plan.get("aggregation", "none") if plan else "none"
    plan_chart = plan.get("chart_type", "") if plan else ""

    # Detect time-like columns by name
    time_like = [c for c in cols if c.lower() in {"year", "month", "date", "day", "quarter"}]

    # 0. Respect explicit chart_type from plan (user asked for it)
    if plan_chart in ("pie", "line", "bar", "scatter", "histogram", "horizontal_bar", "grouped_bar"):
        # Validate it's feasible
        if plan_chart == "pie" and categorical_cols and numeric_cols:
            return "pie"
        if plan_chart == "line" and numeric_cols:
            return "line"
        if plan_chart == "scatter" and len(numeric_cols) >= 2:
            return "scatter"
        if plan_chart in ("bar", "horizontal_bar", "grouped_bar") and numeric_cols:
            return plan_chart

    # 1. Time series detection
    if datetime_cols and numeric_cols:
        return "line"
    if time_like and numeric_cols:
        return "line"

    # 2. Single numeric value → KPI metric
    if len(df) == 1 and len(numeric_cols) >= 1 and len(categorical_cols) == 0:
        return "metric"

    # 3. Ranking queries (Top N) → horizontal bar
    if plan and plan.get("limit") and aggregation in {"sum", "avg", "count", "min", "max"}:
        if len(categorical_cols) == 1 and len(numeric_cols) >= 1:
            return "horizontal_bar"

    # 4. Category vs single numeric
    if len(categorical_cols) == 1 and len(numeric_cols) == 1:
        unique_vals = df[categorical_cols[0]].nunique()
        if unique_vals <= 6 and aggregation in {"sum", "count"}:
            return "pie"
        if unique_vals <= 10:
            return "bar"
        # Always show a chart — use horizontal bar for many categories
        return "horizontal_bar"

    # 5. Category vs multiple numeric → grouped bar
    if len(categorical_cols) == 1 and len(numeric_cols) > 1:
        return "grouped_bar"

    # 6. Two numeric columns → scatter
    if len(numeric_cols) == 2 and len(categorical_cols) == 0:
        return "scatter"

    # 7. Many rows with numeric → histogram
    if len(numeric_cols) >= 1 and len(df) > 50 and len(categorical_cols) == 0:
        return "histogram"

    # Fallback
    if n_cols >= 2 and numeric_cols:
        return "bar"

    return "table"


def choose_chart(df):
    return determine_chart_type(df)


def create_chart(df, chart, plan=None):
    cols = list(df.columns)

    if chart == "metric":
        return None  # handled separately by render_kpi_metric

    if chart == "line":
        time_cols = [c for c in cols if c.lower() in {"year", "month", "date", "day", "quarter"}]
        datetime_cols = df.select_dtypes(include=["datetime"]).columns.tolist()
        x_col = datetime_cols[0] if datetime_cols else (time_cols[0] if time_cols else None)

        if not x_col:
            return None

        y_candidates = [c for c in cols if c != x_col and df[c].dtype != "object"]
        color_candidates = [c for c in cols if c != x_col and df[c].dtype == "object"]

        y_col = y_candidates[0] if y_candidates else None
        color_col = color_candidates[0] if color_candidates else None

        if not y_col:
            return None

        if color_col:
            fig = px.line(df, x=x_col, y=y_col, color=color_col, markers=True)
        else:
            fig = px.line(df, x=x_col, y=y_col, markers=True)

        fig.update_traces(line=dict(width=3), marker=dict(size=8))
        fig.update_layout(height=500)
        return fig

    if chart == "bar":
        cat_cols = [c for c in cols if df[c].dtype == "object"]
        num_cols = [c for c in cols if df[c].dtype != "object"]

        if len(cat_cols) >= 1 and len(num_cols) >= 1:
            fig = px.bar(df, x=cat_cols[0], y=num_cols[0])
        elif len(num_cols) >= 2:
            fig = px.bar(df, x=num_cols[0], y=num_cols[1])
            fig.update_traces(marker_line_width=0, opacity=0.92)
        else:
            return None

        fig.update_layout(height=500)
        return fig

    if chart == "horizontal_bar":
        cat_cols = [c for c in cols if df[c].dtype == "object"]
        num_cols = [c for c in cols if df[c].dtype != "object"]

        if len(cat_cols) >= 1 and len(num_cols) >= 1:
            sorted_df = df.sort_values(num_cols[0], ascending=True)
            fig = px.bar(sorted_df, x=num_cols[0], y=cat_cols[0], orientation="h")
        else:
            return None

        fig.update_layout(height=max(400, len(df) * 30))
        return fig

    if chart == "grouped_bar":
        cat_cols = [c for c in cols if df[c].dtype == "object"]
        num_cols = [c for c in cols if df[c].dtype != "object"]

        if len(cat_cols) >= 1 and len(num_cols) >= 1:
            fig = px.bar(df, x=cat_cols[0], y=num_cols, barmode="group")
            fig.update_layout(height=500)
            return fig
        return None

    if chart == "scatter":
        num_cols = [c for c in cols if df[c].dtype != "object"]
        if len(num_cols) >= 2:
            fig = px.scatter(df, x=num_cols[0], y=num_cols[1])
            fig.update_layout(height=500)
            return fig
        return None

    if chart == "histogram":
        num_cols = [c for c in cols if df[c].dtype != "object"]
        if num_cols:
            fig = px.histogram(df, x=num_cols[0])
            fig.update_layout(height=500)
            return fig
        return None

    if chart == "pie":
        cat_cols = [c for c in cols if df[c].dtype == "object"]
        num_cols = [c for c in cols if df[c].dtype != "object"]
        if cat_cols and num_cols:
            fig = px.pie(df, names=cat_cols[0], values=num_cols[0])
            fig.update_layout(height=500)
            return fig
        if len(cols) >= 2:
            fig = px.pie(df, names=cols[0], values=cols[1])
            fig.update_layout(height=500)
            return fig
        return None

    return None


def create_gauge_chart(value, label="Value"):
    """Create a nice gauge/indicator chart for single scalar values."""
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return None

    fig = go.Figure(go.Indicator(
        mode="number+delta",
        value=value,
        title={"text": label, "font": {"size": 18, "color": "#94a3b8"}},
        number={"font": {"size": 48, "color": "#f1f5f9"},
                "valueformat": ",.0f" if (isinstance(value, float) and value.is_integer()) or isinstance(value, int) else ",.2f"},
    ))
    fig.update_layout(
        height=180,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#cbd5e1",
        margin=dict(l=20, r=20, t=50, b=20),
    )
    return fig


def render_kpi_metric(df):
    if df is None or df.empty:
        return
    numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
    if len(df) == 1 and numeric_cols:
        for col in numeric_cols:
            val = df.iloc[0][col]
            if abs(val) >= 1_000_000:
                display = f"{val:,.2f}"
            elif float(val).is_integer():
                display = f"{int(val):,}"
            else:
                display = f"{val:,.2f}"
            st.metric(label=col, value=display)


def create_frequency_chart(df, x_col, y_col="frequency"):
    if x_col not in df.columns or y_col not in df.columns:
        return None
    fig = px.bar(df, x=x_col, y=y_col)
    fig.update_layout(height=500)
    return fig


def render_metrics(df):
    numeric_cols = df.select_dtypes(include="number").columns.tolist()

    if len(df) == 0:
        return

    k1, k2, k3 = st.columns(3)

    with k1:
        st.markdown(
            f"""
            <div class="metric-pill">
                <div class="metric-label">Rows Returned</div>
                <div class="metric-value">{len(df)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with k2:
        first_col = df.columns[0]
        unique_count = df[first_col].nunique() if first_col in df.columns else 0
        st.markdown(
            f"""
            <div class="metric-pill">
                <div class="metric-label">Unique {first_col}</div>
                <div class="metric-value">{unique_count}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with k3:
        if numeric_cols:
            total_val = round(df[numeric_cols[0]].sum(), 2)
            label = f"Total {numeric_cols[0]}"
            value = total_val
        else:
            label = "Numeric Summary"
            value = "N/A"

        st.markdown(
            f"""
            <div class="metric-pill">
                <div class="metric-label">{label}</div>
                <div class="metric-value">{value}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)