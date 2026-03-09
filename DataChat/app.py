import os
import html as html_lib
from datetime import datetime

import google.generativeai as genai
import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError

from chart_utils import (
    create_chart,
    create_frequency_chart,
    choose_chart,
    determine_chart_type,
    render_kpi_metric,
    render_metrics,
)
from dataset_manager import list_tables, preview_table, save_uploaded_csv
from db_utils import DEFAULT_TABLE, get_column_types, get_columns, get_row_count, run_query
from followup import is_followup_question, refine_query_plan
from metadata_handlers import (
    classify_intent,
    get_column_datatype,
    get_dataset_overview,
    get_null_count,
    get_sample_values,
    get_top_values,
    get_unique_count,
)
from planner import build_sql_from_plan, generate_query_plan, summarize_plan
from state_manager import (
    clear_followup_context,
    get_active_table,
    get_last_plan,
    get_last_question,
    init_session_state,
    set_active_table,
    set_last_plan,
    set_last_question,
    set_last_sql,
)
from ui import load_ui

load_ui()
init_session_state()

from error_handlers import format_user_error
from insight_generator import generate_result_highlights, generate_result_summary, format_value
from schema_utils import get_schema_profile


# ── Session state for chat ──────────────────────────────────────────
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []


# ── API key ─────────────────────────────────────────────────────────
def load_api_key():
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("API_KEY") or os.getenv("GOOGLE_API_KEY")
    if api_key:
        return api_key
    try:
        return st.secrets["API_KEY"]
    except (StreamlitSecretNotFoundError, KeyError):
        return None


def validate_sql(sql):
    cleaned_sql = sql.strip().rstrip(";")
    lowered_sql = cleaned_sql.lower()
    if not lowered_sql.startswith("select"):
        raise ValueError("Only SELECT queries are allowed.")
    blocked_terms = ["insert", "update", "delete", "drop", "alter", "truncate", "attach", "pragma"]
    if any(term in lowered_sql for term in blocked_terms):
        raise ValueError("Unsafe SQL was generated and blocked.")
    return cleaned_sql


api_key = load_api_key()
if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.5-flash")
else:
    model = None


# ── Business logic ──────────────────────────────────────────────────
def process_business_question(question):
    active_table = get_active_table()
    columns = get_columns(active_table)
    intent = classify_intent(question, columns)

    if intent == "schema":
        row_count, schema_df = get_dataset_overview(active_table)
        return {"type": "schema", "row_count": row_count, "schema_df": schema_df}
    elif intent == "sample_values":
        column_name, limit, sql, df = get_sample_values(question, active_table)
        return {"type": "sample_values", "column_name": column_name, "limit": limit, "sql": sql, "df": df}
    elif intent == "column_type":
        column_name, dtype = get_column_datatype(question, active_table)
        return {"type": "column_type", "column_name": column_name, "dtype": dtype}
    elif intent == "unique_count":
        column_name, sql, unique_count = get_unique_count(question, active_table)
        return {"type": "unique_count", "column_name": column_name, "sql": sql, "unique_count": unique_count}
    elif intent == "null_count":
        column_name, sql, null_count = get_null_count(question, active_table)
        return {"type": "null_count", "column_name": column_name, "sql": sql, "null_count": null_count}
    elif intent == "top_values":
        column_name, limit, sql, df = get_top_values(question, active_table)
        return {"type": "top_values", "column_name": column_name, "limit": limit, "sql": sql, "df": df}
    else:
        schema_profile = get_schema_profile(active_table)
        column_types = {col["name"]: col["type"] for col in schema_profile["columns"]}

        last_plan = get_last_plan()
        if last_plan and is_followup_question(question):
            plan = refine_query_plan(
                question=question, previous_plan=last_plan, model=model,
                table_name=active_table, column_types=column_types, schema_profile=schema_profile,
            )
        else:
            plan = generate_query_plan(
                question=question, model=model, table_name=active_table,
                column_types=column_types, schema_profile=schema_profile,
            )

        sql = validate_sql(build_sql_from_plan(plan, active_table))
        df = run_query(sql)
        set_last_plan(plan)
        set_last_question(question)
        set_last_sql(sql)
        return {"type": "dashboard", "plan": plan, "sql": sql, "df": df}


# ── Render results into the dashboard column ────────────────────────
def render_result(result):
    rtype = result["type"]

    if rtype == "schema":
        st.markdown(f'<div class="insight-box">Dataset <b>{get_active_table()}</b> has <b>{result["row_count"]}</b> rows and <b>{len(result["schema_df"])}</b> columns.</div>', unsafe_allow_html=True)
        st.dataframe(result["schema_df"], use_container_width=True)

    elif rtype == "sample_values":
        st.markdown(f'<div class="sql-block">{html_lib.escape(result["sql"])}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="insight-box">Showing up to {result["limit"]} distinct values from <b>{result["column_name"]}</b></div>', unsafe_allow_html=True)
        st.dataframe(result["df"], use_container_width=True)

    elif rtype == "column_type":
        st.markdown(f'<div class="insight-box"><b>{result["column_name"]}</b> has datatype: <b>{result["dtype"]}</b></div>', unsafe_allow_html=True)

    elif rtype == "unique_count":
        st.markdown(f'<div class="sql-block">{html_lib.escape(result["sql"])}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="insight-box"><b>{result["column_name"]}</b> has <b>{result["unique_count"]}</b> unique values.</div>', unsafe_allow_html=True)

    elif rtype == "null_count":
        st.markdown(f'<div class="sql-block">{html_lib.escape(result["sql"])}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="insight-box"><b>{result["column_name"]}</b> has <b>{result["null_count"]}</b> null values.</div>', unsafe_allow_html=True)

    elif rtype == "top_values":
        df = result["df"]
        st.markdown(f'<div class="sql-block">{html_lib.escape(result["sql"])}</div>', unsafe_allow_html=True)

        summary = generate_result_summary(df, {"chart_type": "bar"})
        if summary:
            st.markdown(f'<div class="insight-box">{html_lib.escape(summary)}</div>', unsafe_allow_html=True)

        st.dataframe(df, use_container_width=True)

        fig = create_frequency_chart(df, result["column_name"], "frequency")
        if fig is not None:
            _style_fig(fig)
            st.plotly_chart(fig, use_container_width=True, config=_chart_config())

    elif rtype == "dashboard":
        plan = result["plan"]
        sql = result["sql"]
        df = result["df"]

        # Badges
        smart_chart = determine_chart_type(df, plan)
        agg = plan.get("aggregation", "none")
        badges = f'<span class="badge badge-green">✓ SQL valid</span>'
        if smart_chart != "table":
            badges += f' <span class="badge">{smart_chart} chart</span>'
        if agg != "none":
            badges += f' <span class="badge">{agg.upper()}</span>'
        if plan.get("limit"):
            badges += f' <span class="badge">LIMIT {plan["limit"]}</span>'
        st.markdown(f'<div class="badge-row">{badges}</div>', unsafe_allow_html=True)

        # SQL
        st.markdown(f'<div class="sql-block">{html_lib.escape(sql)}</div>', unsafe_allow_html=True)

        if df.empty:
            st.warning("The query ran successfully, but it returned no rows.")
            return

        # KPI cards for scalar/aggregate results
        import numpy as np
        numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
        cat_cols = [c for c in df.columns if df[c].dtype == "object"]

        import pandas as pd_check
        all_null = len(df) == 1 and numeric_cols and all(pd_check.isna(df.iloc[0][c]) for c in numeric_cols)

        if all_null:
            st.warning("The query returned NULL — the filter values may not match any rows. Check exact spellings in the dataset.")
        elif smart_chart == "metric" or (len(df) == 1 and numeric_cols):
            kpi_html = '<div class="kpi-row">'
            for col in numeric_cols:
                val = df.iloc[0][col]
                kpi_html += f'<div class="kpi-card"><div class="kpi-label">{html_lib.escape(col)}</div><div class="kpi-value">{format_value(val)}</div></div>'
            if cat_cols:
                for col in cat_cols:
                    kpi_html += f'<div class="kpi-card"><div class="kpi-label">{html_lib.escape(col)}</div><div class="kpi-value">{html_lib.escape(str(df.iloc[0][col]))}</div></div>'
            kpi_html += '</div>'
            st.markdown(kpi_html, unsafe_allow_html=True)

        # Summary insight
        summary = generate_result_summary(df, plan)
        if summary:
            st.markdown(f'<div class="insight-box">{html_lib.escape(summary)}</div>', unsafe_allow_html=True)

        # Highlights
        highlights = generate_result_highlights(df, plan)
        if highlights:
            for item in highlights:
                st.markdown(f'<div class="highlight-item">{item}</div>', unsafe_allow_html=True)

        # Data table (show when more than 1 row)
        if len(df) > 1:
            with st.expander(f"📋 Data Table ({len(df)} rows)", expanded=False):
                st.dataframe(df, use_container_width=True)

        # Chart
        if smart_chart == "metric" or (len(df) == 1 and numeric_cols and not all_null):
            # Show gauge chart for single-value metrics
            from chart_utils import create_gauge_chart
            for col in numeric_cols:
                val = df.iloc[0][col]
                if not pd_check.isna(val):
                    fig = create_gauge_chart(val, col)
                    if fig:
                        st.plotly_chart(fig, use_container_width=True, config=_chart_config())
        else:
            chart = smart_chart
            fig = create_chart(df, chart, plan)
            if fig is not None:
                _style_fig(fig)
                st.plotly_chart(fig, use_container_width=True, config=_chart_config())


def _style_fig(fig):
    """Apply dark theme to plotly figure."""
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#cbd5e1",
        margin=dict(l=20, r=20, t=40, b=20),
        legend=dict(bgcolor="rgba(0,0,0,0)", font_color="#94a3b8"),
    )
    fig.update_xaxes(gridcolor="rgba(255,255,255,0.05)", zerolinecolor="rgba(255,255,255,0.05)")
    fig.update_yaxes(gridcolor="rgba(255,255,255,0.05)", zerolinecolor="rgba(255,255,255,0.05)")


def _chart_config():
    return {
        "displaylogo": False,
        "toImageButtonOptions": {"format": "png", "filename": "datachat_chart", "height": 600, "width": 1000, "scale": 2},
    }


# ── Build a text summary for chat history ───────────────────────────
def build_reply_text(result):
    rtype = result["type"]
    if rtype == "schema":
        return f"Dataset **{get_active_table()}** has **{result['row_count']}** rows and **{len(result['schema_df'])}** columns. Check the dashboard panel for full details."
    elif rtype == "column_type":
        return f"**{result['column_name']}** has datatype: **{result['dtype']}**"
    elif rtype == "unique_count":
        return f"**{result['column_name']}** has **{result['unique_count']}** unique values."
    elif rtype == "null_count":
        return f"**{result['column_name']}** has **{result['null_count']}** null values."
    elif rtype == "sample_values":
        return f"Here are {result['limit']} sample values from **{result['column_name']}**. See the dashboard for the full table."
    elif rtype == "top_values":
        df = result["df"]
        summary = generate_result_summary(df, {"chart_type": "bar"})
        extra = ""
        highlights = generate_result_highlights(df, {"chart_type": "bar"})
        if highlights:
            extra = " | " + " · ".join(h.replace("**", "") for h in highlights[:3])
        return (summary or f"Top {result['limit']} values from {result['column_name']}.") + extra
    elif rtype == "dashboard":
        df = result["df"]
        plan = result["plan"]
        if df.empty:
            return "The query ran successfully but returned no rows."
        summary = generate_result_summary(df, plan)
        highlights = generate_result_highlights(df, plan)
        parts = [summary or f"Query returned {len(df)} rows."]
        if highlights:
            parts.append(" · ".join(h.replace("**", "") for h in highlights[:3]))
        return " | ".join(parts)
    return "Done."


# ════════════════════════════════════════════════════════════════════
#  MAIN APP LAYOUT
# ════════════════════════════════════════════════════════════════════

# Top bar
active_tbl = get_active_table()
st.markdown(f"""
<div class="topbar">
    <div class="topbar-logo">📊 DataChat</div>
    <div class="topbar-status">
        <span class="status-dot"></span> gemini-2.5-flash connected &nbsp;·&nbsp; Active: {html_lib.escape(active_tbl)}
    </div>
</div>
""", unsafe_allow_html=True)


# Sidebar ── Dataset Manager
with st.sidebar:
    st.markdown("## 📁 Datasets")
    uploaded_file = st.file_uploader("Upload CSV", type=["csv"])
    if uploaded_file is not None:
        if st.button("Load CSV"):
            try:
                table_name, df_uploaded = save_uploaded_csv(uploaded_file)
                set_active_table(table_name)
                clear_followup_context()
                st.success(f"Loaded as `{table_name}`")
                st.rerun()
            except Exception as e:
                st.error(str(e))

    available_tables = list_tables()
    if DEFAULT_TABLE not in available_tables:
        available_tables = [DEFAULT_TABLE] + available_tables
    current_active = get_active_table()
    if current_active not in available_tables:
        current_active = DEFAULT_TABLE
        set_active_table(current_active)

    selected_table = st.selectbox("Active dataset", options=available_tables, index=available_tables.index(current_active))
    if selected_table != current_active:
        set_active_table(selected_table)
        clear_followup_context()
        st.rerun()

    st.markdown("---")
    try:
        row_count = get_row_count(get_active_table())
        columns = get_columns(get_active_table())
        st.caption(f"Rows: {row_count} · Columns: {len(columns)}")
    except Exception:
        pass

    st.markdown("### Quick prompts")
    prompts = [
        "What columns are in this dataset?",
        "Show top 10 values from life_insurer",
        "Show total claims paid amount by life insurer",
        "Total claims of 2023",
        "Now only for 2023",
    ]
    for p in prompts:
        if st.button(p, key=f"sp_{p}"):
            st.session_state.pending_question = p
            st.rerun()

    st.markdown("---")
    if st.button("🗑️ Clear chat"):
        st.session_state.chat_history = []
        clear_followup_context()
        st.rerun()


# ── Layout: Chat (left) + Dashboard (right) ────────────────────────
chat_col, dash_col = st.columns([1, 2], gap="medium")

with chat_col:
    st.markdown("#### 💬 Conversation")

    # Render chat messages
    chat_container = st.container(height=480)
    with chat_container:
        if not st.session_state.chat_history:
            st.markdown('<div class="msg-bot">Hi! Ask me anything about your data. Type a question or click the 🎤 mic to speak.</div>', unsafe_allow_html=True)

        for msg in st.session_state.chat_history:
            ts = msg.get("time", "")
            if msg["role"] == "user":
                st.markdown(f'<div class="msg-user">{html_lib.escape(msg["text"])}<div class="msg-time">{ts}</div></div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="msg-bot">{msg["text"]}<div class="msg-time">{ts}</div></div>', unsafe_allow_html=True)

    # ── Speech-to-text via browser Web Speech API ───────────────────
    st.components.v1.html("""
    <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">
        <button id="mic-btn" onclick="toggleMic()" style="
            width:42px;height:42px;border-radius:50%;border:none;
            background:linear-gradient(135deg,#7c3aed,#6d28d9);
            color:white;font-size:1.2rem;cursor:pointer;
            box-shadow:0 4px 12px rgba(124,58,237,0.3);
            transition:all 0.2s;display:flex;align-items:center;justify-content:center;
        ">🎤</button>
        <span id="mic-status" style="color:#64748b;font-size:0.82rem;">Click mic to speak</span>
    </div>
    <script>
    let recognition = null;
    let isListening = false;

    function toggleMic() {
        if (isListening) { stopMic(); return; }
        if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
            document.getElementById('mic-status').textContent = 'Speech not supported in this browser';
            return;
        }
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        recognition = new SpeechRecognition();
        recognition.lang = 'en-US';
        recognition.interimResults = false;
        recognition.continuous = false;

        recognition.onstart = () => {
            isListening = true;
            document.getElementById('mic-btn').style.background = 'linear-gradient(135deg,#ef4444,#dc2626)';
            document.getElementById('mic-btn').style.animation = 'pulse-mic 1.2s infinite';
            document.getElementById('mic-status').textContent = 'Listening...';
        };
        recognition.onresult = (e) => {
            const transcript = e.results[0][0].transcript;
            document.getElementById('mic-status').textContent = 'Heard: ' + transcript;
            // Send to Streamlit via query params workaround
            const input = window.parent.document.querySelector('input[data-testid="stTextInput"][aria-label="Ask a question..."]')
                || window.parent.document.querySelector('input[aria-label="Ask a question..."]');
            if (input) {
                const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.parent.HTMLInputElement.prototype, 'value').set;
                nativeInputValueSetter.call(input, transcript);
                input.dispatchEvent(new Event('input', { bubbles: true }));
                // Auto-submit after a short delay
                setTimeout(() => {
                    const form = input.closest('form');
                    if (form) form.requestSubmit();
                }, 300);
            }
        };
        recognition.onerror = (e) => {
            document.getElementById('mic-status').textContent = 'Error: ' + e.error;
            stopMic();
        };
        recognition.onend = () => { stopMic(); };
        recognition.start();
    }

    function stopMic() {
        isListening = false;
        if (recognition) recognition.stop();
        document.getElementById('mic-btn').style.background = 'linear-gradient(135deg,#7c3aed,#6d28d9)';
        document.getElementById('mic-btn').style.animation = 'none';
        if (document.getElementById('mic-status').textContent === 'Listening...') {
            document.getElementById('mic-status').textContent = 'Click mic to speak';
        }
    }
    </script>
    <style>
    @keyframes pulse-mic {
        0%,100% { box-shadow: 0 0 0 0 rgba(239,68,68,0.5); }
        50% { box-shadow: 0 0 0 12px rgba(239,68,68,0); }
    }
    </style>
    """, height=50)

    # ── Text input ──────────────────────────────────────────────────
    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_input("Ask a question...", placeholder="e.g. Total claims of 2023", label_visibility="collapsed")
        submitted = st.form_submit_button("Send ➤")

    # Handle pending question from sidebar prompt buttons
    pending = st.session_state.pop("pending_question", None)
    if pending:
        user_input = pending
        submitted = True

    # ── Process the question ────────────────────────────────────────
    if submitted and user_input and user_input.strip():
        question = user_input.strip()
        now = datetime.now().strftime("%I:%M %p")

        # Add user message
        st.session_state.chat_history.append({"role": "user", "text": question, "time": now})

        try:
            result = process_business_question(question)
            reply = build_reply_text(result)
            st.session_state.chat_history.append({"role": "bot", "text": reply, "time": now})
            st.session_state.last_result = result
            # Store reply for TTS – strip markdown and emoji
            import re as _re
            _clean = reply.replace("**", "").replace("*", "")
            _clean = _re.sub(r'[\U0001f300-\U0001f9ff\u2600-\u27bf\u2300-\u23ff\u200d\ufe0f]', '', _clean)
            st.session_state.tts_text = _clean.strip()
        except Exception as e:
            active_table_name = get_active_table()
            available_columns = []
            try:
                available_columns = get_columns(active_table_name)
            except Exception:
                pass
            err_msg = format_user_error(error=e, active_table=active_table_name, columns=available_columns)
            st.session_state.chat_history.append({"role": "bot", "text": f"⚠️ {err_msg}", "time": now})
            st.session_state.last_result = None

        st.rerun()

# ── Text-to-Speech: speak the last bot response ────────────────────
tts_text = st.session_state.pop("tts_text", None)
if tts_text:
    safe_tts = html_lib.escape(tts_text).replace("\n", " ").replace("'", "\\'")
    st.components.v1.html(f"""
    <script>
    (function() {{
        const synth = window.parent.speechSynthesis;
        if (!synth) return;
        synth.cancel();

        function speakWithVoice() {{
            const voices = synth.getVoices();
            const utter = new SpeechSynthesisUtterance('{safe_tts}');
            // Prefer natural / high-quality voices
            const preferred = [
                'Google US English',
                'Google UK English Female',
                'Microsoft Zira',
                'Microsoft Jenny',
                'Samantha',
                'Karen',
                'Daniel'
            ];
            let chosen = null;
            for (const name of preferred) {{
                chosen = voices.find(v => v.name.includes(name));
                if (chosen) break;
            }}
            // Fallback: pick any English female voice
            if (!chosen) {{
                chosen = voices.find(v => v.lang.startsWith('en') && v.name.toLowerCase().includes('female'));
            }}
            if (!chosen) {{
                chosen = voices.find(v => v.lang.startsWith('en'));
            }}
            if (chosen) utter.voice = chosen;
            utter.rate = 0.95;
            utter.pitch = 1.05;
            utter.volume = 1.0;
            utter.lang = 'en-US';
            synth.speak(utter);
        }}

        // Voices may load async – wait for them
        if (synth.getVoices().length) {{
            speakWithVoice();
        }} else {{
            synth.onvoiceschanged = speakWithVoice;
        }}
    }})();
    </script>
    """, height=0)

# ── Dashboard panel (right) ─────────────────────────────────────────
with dash_col:
    last_result = st.session_state.get("last_result")
    if last_result:
        title = "Results"
        if last_result["type"] == "dashboard":
            title = last_result.get("plan", {}).get("title", "Dashboard")
        st.markdown(f"#### 📊 {title}")
        render_result(last_result)
    else:
        st.markdown("#### 📊 Dashboard")
        st.markdown('<div class="insight-box">Ask a question in the chat to see results here.</div>', unsafe_allow_html=True)
        st.markdown("")
        st.markdown("**Example queries:**")
        st.markdown("- Show total claims paid amount by life insurer")
        st.markdown("- Total claims of 2023")
        st.markdown("- Show top 10 values from life_insurer")
        st.markdown("- What columns are in this dataset?")