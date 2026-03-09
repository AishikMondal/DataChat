import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ── Shared palette & helpers ───────────────────────────────────────────────
_COLORS = [
    "#818cf8", "#60a5fa", "#34d399", "#f472b6",
    "#fb923c", "#a78bfa", "#38bdf8", "#4ade80",
    "#f87171", "#facc15", "#2dd4bf", "#c084fc",
]

_PIE_COLORS = [
    "#6366f1", "#3b82f6", "#10b981", "#ec4899",
    "#f59e0b", "#8b5cf6", "#06b6d4", "#22c55e",
    "#64748b",  # "Others" slice — neutral gray
]

# Max slices before collapsing into "Others"
_PIE_MAX_SLICES = 8

_DARK_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, sans-serif", color="#cbd5e1", size=12),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#94a3b8")),
    xaxis=dict(
        gridcolor="rgba(255,255,255,0.05)",
        zerolinecolor="rgba(255,255,255,0.06)",
        tickfont=dict(size=11, color="#94a3b8"),
        title_font=dict(size=12, color="#64748b"),
        linecolor="rgba(255,255,255,0.06)",
    ),
    yaxis=dict(
        gridcolor="rgba(255,255,255,0.05)",
        zerolinecolor="rgba(255,255,255,0.06)",
        tickfont=dict(size=11, color="#94a3b8"),
        title_font=dict(size=12, color="#64748b"),
    ),
    margin=dict(l=50, r=30, t=50, b=80),
)


def _apply_dark(fig, extra_layout: dict | None = None):
    """Apply dark‐theme layout to any figure."""
    layout = dict(_DARK_LAYOUT)
    if extra_layout:
        layout.update(extra_layout)
    fig.update_layout(**layout)
    return fig


def _label_angle(n: int) -> int:
    """Choose x-axis tick rotation based on number of categories."""
    if n <= 5:
        return 0
    if n <= 10:
        return -30
    return -55


def _bar_colors(n: int) -> list[str]:
    return [_COLORS[i % len(_COLORS)] for i in range(n)]


def _collapse_pie(df: pd.DataFrame, name_col: str, val_col: str, max_slices: int = _PIE_MAX_SLICES) -> pd.DataFrame:
    """Keep the top max_slices-1 rows and merge the rest into 'Others'."""
    df = df.copy().dropna(subset=[val_col])
    df[val_col] = pd.to_numeric(df[val_col], errors="coerce").fillna(0)
    df = df.sort_values(val_col, ascending=False).reset_index(drop=True)
    if len(df) <= max_slices:
        return df
    top = df.iloc[: max_slices - 1].copy()
    others_val = df.iloc[max_slices - 1 :][val_col].sum()
    others_row = pd.DataFrame({name_col: ["Others"], val_col: [others_val]})
    return pd.concat([top, others_row], ignore_index=True)


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
            fig = px.line(df, x=x_col, y=y_col, color=color_col, markers=True,
                          color_discrete_sequence=_COLORS)
        else:
            fig = px.line(df, x=x_col, y=y_col, markers=True,
                          color_discrete_sequence=_COLORS)

        fig.update_traces(line=dict(width=3), marker=dict(size=8))
        _apply_dark(fig, {"height": 420})
        return fig

    if chart == "bar":
        cat_cols = [c for c in cols if df[c].dtype == "object"]
        num_cols = [c for c in cols if df[c].dtype != "object"]

        if not (cat_cols and num_cols):
            if len(num_cols) >= 2:
                x_col, y_col = num_cols[0], num_cols[1]
            else:
                return None
        else:
            x_col, y_col = cat_cols[0], num_cols[0]

        n = len(df)
        angle = _label_angle(n)
        colors = _bar_colors(n)

        fig = go.Figure(go.Bar(
            x=df[x_col],
            y=df[y_col],
            marker=dict(
                color=colors,
                line=dict(color="rgba(255,255,255,0.08)", width=1),
            ),
            text=[f"{v:,.0f}" if isinstance(v, (int, float)) and not (isinstance(v, float) and np.isnan(v)) else ""
                  for v in df[y_col]],
            textposition="outside",
            textfont=dict(size=10, color="#94a3b8"),
            hovertemplate=f"<b>%{{x}}</b><br>{y_col}: %{{y:,.2f}}<extra></extra>",
        ))
        _apply_dark(fig, {
            "height": 420,
            "xaxis": dict(
                **_DARK_LAYOUT["xaxis"],
                tickangle=angle,
                title=dict(text=x_col, font=dict(size=12, color="#64748b")),
                automargin=True,
            ),
            "yaxis": dict(
                **_DARK_LAYOUT["yaxis"],
                title=dict(text=y_col, font=dict(size=12, color="#64748b")),
            ),
            "margin": dict(l=60, r=30, t=40, b=max(80, 20 + n * 4)),
            "bargap": 0.3,
        })
        return fig

    if chart == "horizontal_bar":
        cat_cols = [c for c in cols if df[c].dtype == "object"]
        num_cols = [c for c in cols if df[c].dtype != "object"]

        if not (cat_cols and num_cols):
            return None

        sorted_df = df.sort_values(num_cols[0], ascending=True)
        n = len(sorted_df)
        colors = _bar_colors(n)

        fig = go.Figure(go.Bar(
            x=sorted_df[num_cols[0]],
            y=sorted_df[cat_cols[0]],
            orientation="h",
            marker=dict(
                color=colors[::-1],
                line=dict(color="rgba(255,255,255,0.08)", width=1),
            ),
            text=[f"{v:,.0f}" if isinstance(v, (int, float)) and not (isinstance(v, float) and np.isnan(v)) else ""
                  for v in sorted_df[num_cols[0]]],
            textposition="outside",
            textfont=dict(size=10, color="#94a3b8"),
            hovertemplate=f"<b>%{{y}}</b><br>{num_cols[0]}: %{{x:,.2f}}<extra></extra>",
        ))
        _apply_dark(fig, {
            "height": max(380, n * 32 + 100),
            "xaxis": dict(
                **_DARK_LAYOUT["xaxis"],
                title=dict(text=num_cols[0], font=dict(size=12, color="#64748b")),
            ),
            "yaxis": {
                **_DARK_LAYOUT["yaxis"],
                **{"title": None, "tickfont": dict(size=11, color="#cbd5e1"), "automargin": True},
            },
            "margin": dict(l=20, r=80, t=40, b=50),
            "bargap": 0.25,
        })
        return fig

    if chart == "grouped_bar":
        cat_cols = [c for c in cols if df[c].dtype == "object"]
        num_cols = [c for c in cols if df[c].dtype != "object"]

        if not (cat_cols and num_cols):
            return None

        n = len(df)
        angle = _label_angle(n)

        fig = go.Figure()
        for i, nc in enumerate(num_cols):
            fig.add_trace(go.Bar(
                name=nc,
                x=df[cat_cols[0]],
                y=df[nc],
                marker_color=_COLORS[i % len(_COLORS)],
                hovertemplate=f"<b>%{{x}}</b><br>{nc}: %{{y:,.2f}}<extra></extra>",
            ))
        fig.update_layout(barmode="group")
        _apply_dark(fig, {
            "height": 420,
            "xaxis": dict(
                **_DARK_LAYOUT["xaxis"],
                tickangle=angle,
                title=dict(text=cat_cols[0], font=dict(size=12, color="#64748b")),
                automargin=True,
            ),
            "margin": dict(l=60, r=30, t=40, b=max(80, 20 + n * 4)),
            "bargap": 0.2,
            "bargroupgap": 0.1,
        })
        return fig

    if chart == "scatter":
        num_cols = [c for c in cols if df[c].dtype != "object"]
        cat_cols = [c for c in cols if df[c].dtype == "object"]
        if len(num_cols) >= 2:
            fig = px.scatter(
                df, x=num_cols[0], y=num_cols[1],
                color=cat_cols[0] if cat_cols else None,
                color_discrete_sequence=_COLORS,
                hover_data=df.columns.tolist(),
            )
            fig.update_traces(marker=dict(size=8, opacity=0.8))
            _apply_dark(fig, {"height": 420})
            return fig
        return None

    if chart == "histogram":
        num_cols = [c for c in cols if df[c].dtype != "object"]
        if num_cols:
            fig = px.histogram(df, x=num_cols[0], color_discrete_sequence=_COLORS)
            fig.update_traces(marker=dict(line=dict(color="rgba(255,255,255,0.1)", width=1)))
            _apply_dark(fig, {"height": 420, "bargap": 0.05})
            return fig
        return None

    if chart == "pie":
        cat_cols = [c for c in cols if df[c].dtype == "object"]
        num_cols = [c for c in cols if df[c].dtype != "object"]

        if cat_cols and num_cols:
            name_col, val_col = cat_cols[0], num_cols[0]
        elif len(cols) >= 2:
            name_col, val_col = cols[0], cols[1]
        else:
            return None

        pie_df = _collapse_pie(df, name_col, val_col)
        n = len(pie_df)

        fig = go.Figure(go.Pie(
            labels=pie_df[name_col],
            values=pie_df[val_col],
            hole=0.38,
            marker=dict(
                colors=_PIE_COLORS[:n],
                line=dict(color="#0b0f1e", width=2),
            ),
            textinfo="label+percent",
            textfont=dict(size=12),
            insidetextorientation="radial",
            hovertemplate="<b>%{label}</b><br>Value: %{value:,.2f}<br>Share: %{percent}<extra></extra>",
        ))
        _apply_dark(fig, {
            "height": 420,
            "showlegend": True,
            "legend": dict(
                bgcolor="rgba(0,0,0,0)",
                font=dict(size=11, color="#94a3b8"),
                orientation="v",
                x=1.02,
                y=0.5,
            ),
            "margin": dict(l=20, r=140, t=40, b=20),
        })
        return fig

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

    n = len(df)
    angle = _label_angle(n)
    colors = _bar_colors(n)

    fig = go.Figure(go.Bar(
        x=df[x_col],
        y=df[y_col],
        marker=dict(color=colors, line=dict(color="rgba(255,255,255,0.08)", width=1)),
        text=[f"{v:,.0f}" if isinstance(v, (int, float)) else "" for v in df[y_col]],
        textposition="outside",
        textfont=dict(size=10, color="#94a3b8"),
        hovertemplate=f"<b>%{{x}}</b><br>{y_col}: %{{y:,.0f}}<extra></extra>",
    ))
    _apply_dark(fig, {
        "height": 400,
        "xaxis": dict(
            **_DARK_LAYOUT["xaxis"],
            tickangle=angle,
            title=dict(text=x_col, font=dict(size=12, color="#64748b")),
            automargin=True,
        ),
        "yaxis": dict(
            **_DARK_LAYOUT["yaxis"],
            title=dict(text=y_col, font=dict(size=12, color="#64748b")),
        ),
        "margin": dict(l=60, r=30, t=40, b=max(80, 20 + n * 4)),
        "bargap": 0.3,
    })
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


# ── Multi-chart builder ────────────────────────────────────────────────────
def create_multi_charts(df: pd.DataFrame, plan: dict | None = None) -> list[dict]:
    """Return a list of {type, figure} dicts for all chart types applicable to df."""
    if df is None or df.empty:
        return []

    cols = df.columns.tolist()
    numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
    cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
    datetime_cols = df.select_dtypes(include=["datetime"]).columns.tolist()
    time_like = [c for c in cols if c.lower() in {"year", "month", "date", "day", "quarter"}]

    results: list[dict] = []

    def _add(ct):
        fig = create_chart(df, ct, plan)
        if fig is not None:
            results.append({"type": ct, "figure": fig})

    # Single scalar value → no multi-chart
    if len(df) == 1 and not cat_cols:
        return []

    # Time series: line is primary, bar as alternate
    if (datetime_cols or time_like) and numeric_cols:
        _add("line")
        _add("bar")
        return results

    # Category + numeric data: bar, horizontal_bar, and optionally pie
    if cat_cols and numeric_cols:
        _add("bar")
        _add("horizontal_bar")
        # Pie is useful when the data is a distribution (limited rows)
        if len(df) <= 20:
            _add("pie")
        return results

    # Multiple numeric columns: grouped bar
    if len(numeric_cols) > 1 and not cat_cols:
        _add("grouped_bar")
        _add("scatter")
        return results

    # Fallback: single best chart
    primary = determine_chart_type(df, plan)
    _add(primary)
    return results