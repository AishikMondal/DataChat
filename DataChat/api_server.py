"""
FastAPI backend for DataChat – powers the Next.js / shadcn UI.

Start with:
    uvicorn api_server:app --reload --port 8000
"""
import os
import sys
import json
import re
from pathlib import Path
from typing import Optional, Any

# ── Mock 'streamlit' so chart_utils / state_manager can be imported ───────────
from unittest.mock import MagicMock

_st_mock = MagicMock()
sys.modules.setdefault("streamlit", _st_mock)
sys.modules.setdefault("streamlit.errors", _st_mock)

# ── API Key ────────────────────────────────────────────────────────────────────
def _load_api_key() -> Optional[str]:
    for var in ("GEMINI_API_KEY", "API_KEY", "GOOGLE_API_KEY"):
        v = os.getenv(var)
        if v:
            return v
    # Try .streamlit/secrets.toml
    try:
        import toml  # type: ignore
        secrets = toml.load(Path(__file__).parent / ".streamlit" / "secrets.toml")
        return secrets.get("API_KEY")
    except Exception:
        pass
    # Manual toml-lite parser (no dependency)
    try:
        p = Path(__file__).parent / ".streamlit" / "secrets.toml"
        text = p.read_text()
        for line in text.splitlines():
            line = line.strip()
            if line.startswith("API_KEY"):
                parts = line.split("=", 1)
                if len(parts) == 2:
                    return parts[1].strip().strip('"').strip("'")
    except Exception:
        pass
    return None


import google.generativeai as genai  # noqa: E402  # legacy – still works

api_key = _load_api_key()
if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.5-flash")
else:
    model = None

# ── Project imports ────────────────────────────────────────────────────────────
from chart_utils import (  # noqa: E402
    create_chart,
    create_frequency_chart,
    create_multi_charts,
    determine_chart_type,
    create_gauge_chart,
)
from dataset_manager import list_tables, save_uploaded_csv  # noqa: E402
from db_utils import DEFAULT_TABLE, get_columns, get_column_types, get_row_count, run_query  # noqa: E402
from metadata_handlers import (  # noqa: E402
    classify_intent,
    get_column_datatype,
    get_dataset_overview,
    get_null_count,
    get_sample_values,
    get_top_values,
    get_unique_count,
)
from planner import build_sql_from_plan, generate_query_plan  # noqa: E402
from insight_generator import generate_result_highlights, generate_result_summary, format_value  # noqa: E402
from schema_utils import get_schema_profile  # noqa: E402
from error_handlers import format_user_error  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

# ── FastAPI ────────────────────────────────────────────────────────────────────
import uvicorn  # noqa: E402
from fastapi import FastAPI, File, HTTPException, UploadFile  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from pydantic import BaseModel  # noqa: E402

app = FastAPI(title="DataChat API", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Server-side state (single-user local app) ─────────────────────────────────
_state: dict[str, Any] = {
    "active_table": DEFAULT_TABLE,
    "last_plan": None,
    "last_question": None,
    "last_sql": None,
}


def _get_active_table() -> str:
    return _state["active_table"]


def _set_active_table(table_name: str) -> None:
    _state["active_table"] = table_name
    _state["last_plan"] = None
    _state["last_question"] = None
    _state["last_sql"] = None


# ── Helpers ────────────────────────────────────────────────────────────────────
def _validate_sql(sql: str) -> str:
    cleaned = sql.strip().rstrip(";")
    lowered = cleaned.lower()
    if not lowered.startswith("select"):
        raise ValueError("Only SELECT queries are allowed.")
    blocked = ["insert", "update", "delete", "drop", "alter", "truncate", "attach", "pragma"]
    if any(t in lowered for t in blocked):
        raise ValueError("Unsafe SQL was generated and blocked.")
    return cleaned


def _fig_to_dict(fig) -> Optional[dict]:
    if fig is None:
        return None
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#cbd5e1",
        margin=dict(l=20, r=20, t=40, b=20),
        legend=dict(bgcolor="rgba(0,0,0,0)", font_color="#94a3b8"),
    )
    fig.update_xaxes(
        gridcolor="rgba(255,255,255,0.05)",
        zerolinecolor="rgba(255,255,255,0.05)",
    )
    fig.update_yaxes(
        gridcolor="rgba(255,255,255,0.05)",
        zerolinecolor="rgba(255,255,255,0.05)",
    )
    return json.loads(fig.to_json())


def _is_followup(question: str) -> bool:
    patterns = [
        r"^now\b", r"^only\b", r"^just\b", r"^filter\b",
        r"^make it\b", r"^change\b", r"^instead\b", r"^sort\b",
        r"^group\b", r"^show only\b", r"^for \d{4}\b",
        r"\bonly for\b", r"\bexclude\b", r"\binclude\b",
    ]
    q = question.strip().lower()
    return any(re.search(p, q) for p in patterns)


def _safe_value(v):
    """Convert numpy/pandas scalars to JSON-safe Python types."""
    if v is None:
        return None
    if isinstance(v, float) and (v != v):  # NaN
        return None
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (np.floating,)):
        return float(v)
    if isinstance(v, (np.bool_,)):
        return bool(v)
    return v


def _df_to_table(df: pd.DataFrame) -> dict:
    return {
        "columns": list(df.columns),
        "rows": [[_safe_value(v) for v in row] for row in df.values.tolist()],
    }


# ── Pydantic Models ────────────────────────────────────────────────────────────
class QueryRequest(BaseModel):
    question: str


class SetTableRequest(BaseModel):
    table: str


# ══════════════════════════════════════════════════════════════════════════════
#  ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "model": "gemini-2.5-flash",
        "api_key_configured": bool(api_key),
    }


@app.get("/api/tables")
def get_tables():
    tables = list_tables()
    if DEFAULT_TABLE not in tables:
        tables = [DEFAULT_TABLE] + tables
    return {"tables": tables}


@app.get("/api/tables/active")
def get_active_table_endpoint():
    tbl = _get_active_table()
    try:
        row_count = get_row_count(tbl)
        columns = get_columns(tbl)
        col_types = get_column_types(tbl)
        schema = [{"name": c, "type": col_types.get(c, "TEXT")} for c in columns]
    except Exception:
        row_count = 0
        columns = []
        schema = []
    return {"table": tbl, "row_count": row_count, "columns": columns, "schema": schema}


@app.post("/api/tables/active")
def set_active_table_endpoint(body: SetTableRequest):
    _set_active_table(body.table)
    try:
        row_count = get_row_count(body.table)
        columns = get_columns(body.table)
        col_types = get_column_types(body.table)
        schema = [{"name": c, "type": col_types.get(c, "TEXT")} for c in columns]
    except Exception:
        row_count = 0
        columns = []
        schema = []
    return {"table": body.table, "row_count": row_count, "columns": columns, "schema": schema}


@app.get("/api/tables/{name}/metadata")
def table_metadata(name: str):
    try:
        row_count = get_row_count(name)
        columns = get_columns(name)
        col_types = get_column_types(name)
        schema = [{"name": c, "type": col_types.get(c, "TEXT")} for c in columns]
        return {"table": name, "row_count": row_count, "columns": schema}
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/api/upload")
async def upload_csv(file: UploadFile = File(...)):
    if not (file.filename or "").lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported.")

    class _FakeUpload:
        def __init__(self, content: bytes, name: str):
            self.name = name
            self._content = content

        def getvalue(self):
            return self._content

    content = await file.read()
    fake = _FakeUpload(content, file.filename or "upload.csv")
    try:
        table_name, _ = save_uploaded_csv(fake)  # type: ignore
        _set_active_table(table_name)
        row_count = get_row_count(table_name)
        columns = get_columns(table_name)
        col_types = get_column_types(table_name)
        schema = [{"name": c, "type": col_types.get(c, "TEXT")} for c in columns]
        return {
            "table": table_name,
            "row_count": row_count,
            "columns": columns,
            "schema": schema,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/query")
def query(body: QueryRequest):
    if model is None:
        raise HTTPException(
            status_code=503,
            detail="Gemini API key not configured. Set API_KEY in .streamlit/secrets.toml or env.",
        )

    question = body.question.strip()
    active_table = _get_active_table()
    columns = get_columns(active_table)

    try:
        intent = classify_intent(question, columns)

        # ── Schema info ────────────────────────────────────────────────────────
        if intent == "schema":
            row_count, schema_df = get_dataset_overview(active_table)
            return {
                "type": "schema",
                "reply": f"Dataset **{active_table}** has **{row_count}** rows and **{len(schema_df)}** columns.",
                "row_count": int(row_count),
                "schema": schema_df.to_dict(orient="records"),
            }

        # ── Sample values ──────────────────────────────────────────────────────
        if intent == "sample_values":
            col_name, limit, sql, df = get_sample_values(question, active_table)
            return {
                "type": "sample_values",
                "reply": f"Here are {limit} sample values from **{col_name}**.",
                "column_name": col_name,
                "sql": sql,
                "table": _df_to_table(df),
            }

        # ── Column type ────────────────────────────────────────────────────────
        if intent == "column_type":
            col_name, dtype = get_column_datatype(question, active_table)
            return {
                "type": "column_type",
                "reply": f"**{col_name}** has datatype: **{dtype}**",
                "column_name": col_name,
                "dtype": dtype,
            }

        # ── Unique count ───────────────────────────────────────────────────────
        if intent == "unique_count":
            col_name, sql, unique_count = get_unique_count(question, active_table)
            return {
                "type": "unique_count",
                "reply": f"**{col_name}** has **{unique_count}** unique values.",
                "column_name": col_name,
                "sql": sql,
                "unique_count": int(unique_count),
            }

        # ── Null count ─────────────────────────────────────────────────────────
        if intent == "null_count":
            col_name, sql, null_count = get_null_count(question, active_table)
            return {
                "type": "null_count",
                "reply": f"**{col_name}** has **{null_count}** null values.",
                "column_name": col_name,
                "sql": sql,
                "null_count": int(null_count),
            }

        # ── Top values ─────────────────────────────────────────────────────────
        if intent == "top_values":
            col_name, limit, sql, df = get_top_values(question, active_table)
            summary = generate_result_summary(df, {"chart_type": "bar"})
            highlights = generate_result_highlights(df, {"chart_type": "bar"})
            fig = create_frequency_chart(df, col_name, "frequency")
            return {
                "type": "top_values",
                "reply": summary or f"Top {limit} values from {col_name}.",
                "column_name": col_name,
                "sql": sql,
                "summary": summary,
                "highlights": highlights or [],
                "chart": _fig_to_dict(fig),
                "table": _df_to_table(df),
            }

        # ── Main analytics query ────────────────────────────────────────────────
        schema_profile = get_schema_profile(active_table)
        column_types = {col["name"]: col["type"] for col in schema_profile["columns"]}

        last_plan = _state["last_plan"]
        plan = generate_query_plan(
            question=question,
            model=model,
            table_name=active_table,
            column_types=column_types,
            schema_profile=schema_profile,
        )

        sql = _validate_sql(build_sql_from_plan(plan, active_table))
        df = run_query(sql)
        _state["last_plan"] = plan
        _state["last_question"] = question
        _state["last_sql"] = sql

        smart_chart = determine_chart_type(df, plan)
        agg = plan.get("aggregation", "none")

        # KPI cards
        kpi_cards = []
        numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
        cat_cols = [c for c in df.columns if df[c].dtype == "object"]

        if not df.empty and (smart_chart == "metric" or len(df) == 1):
            for col in numeric_cols:
                val = df.iloc[0][col]
                if not pd.isna(val):
                    kpi_cards.append({
                        "label": col,
                        "value": format_value(val),
                        "raw": float(val),
                    })
            for col in cat_cols:
                kpi_cards.append({
                    "label": col,
                    "value": str(df.iloc[0][col]),
                    "raw": None,
                })

        # Chart — primary + multi-chart alternatives
        chart_json = None
        charts_json: list[dict] = []
        if not df.empty:
            if smart_chart == "metric" or (len(df) == 1 and numeric_cols):
                for col in numeric_cols:
                    val = df.iloc[0][col]
                    if not pd.isna(val):
                        fig = create_gauge_chart(val, col)
                        chart_json = _fig_to_dict(fig)
                        break
            else:
                fig = create_chart(df, smart_chart, plan)
                chart_json = _fig_to_dict(fig)
                # Build all applicable chart types for multi-viz tabs
                multi = create_multi_charts(df, plan)
                if len(multi) > 1:
                    charts_json = [
                        {"type": m["type"], "figure": _fig_to_dict(m["figure"])}
                        for m in multi
                        if m["figure"] is not None
                    ]

        summary = generate_result_summary(df, plan)
        highlights = generate_result_highlights(df, plan)

        parts = [summary or f"Query returned {len(df)} rows."]
        if highlights:
            parts.append(" · ".join(h.replace("**", "") for h in highlights[:3]))
        reply = " | ".join(parts)

        table_data = _df_to_table(df) if len(df) > 1 else None

        badges = [{"label": "SQL valid", "color": "green"}]
        if smart_chart != "table":
            badges.append({"label": f"{smart_chart} chart", "color": "blue"})
        if agg != "none":
            badges.append({"label": agg.upper(), "color": "purple"})
        if plan.get("limit"):
            badges.append({"label": f"LIMIT {plan['limit']}", "color": "gray"})

        return {
            "type": "dashboard",
            "reply": reply,
            "sql": sql,
            "badges": badges,
            "kpi_cards": kpi_cards,
            "chart": chart_json,
            "chart_type": smart_chart,
            "charts": charts_json if charts_json else None,
            "summary": summary,
            "highlights": highlights or [],
            "table": table_data,
            "empty": df.empty,
            "title": plan.get("title", ""),
        }

    except HTTPException:
        raise
    except Exception as e:
        msg = format_user_error(e)
        raise HTTPException(status_code=500, detail=msg)


if __name__ == "__main__":
    uvicorn.run("api_server:app", host="0.0.0.0", port=8000, reload=True)
