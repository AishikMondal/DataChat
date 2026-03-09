import streamlit as st


def load_ui():
    st.set_page_config(
        page_title="DataChat - AI BI Dashboard",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

/* ===== GLOBAL ===== */
*, *::before, *::after { box-sizing: border-box; }
.stApp {
    background: linear-gradient(160deg, #0b0f1e 0%, #101829 50%, #0d1321 100%);
    color: #e2e8f0;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

.block-container {
    padding-top: 0.75rem;
    padding-bottom: 0;
    max-width: 1440px;
}

header[data-testid="stHeader"] { background: transparent; }
footer { display: none; }

/* ===== TOP BAR ===== */
.topbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.65rem 1.4rem;
    background: rgba(12,16,32,0.85);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 14px;
    margin-bottom: 1rem;
    box-shadow: 0 4px 24px rgba(0,0,0,0.25);
}
.topbar-logo {
    font-size: 1.25rem;
    font-weight: 700;
    letter-spacing: -0.3px;
    background: linear-gradient(135deg, #818cf8, #38bdf8);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.topbar-status {
    display: flex; align-items: center; gap: 0.5rem;
    font-size: 0.78rem; color: #64748b; font-weight: 500;
}
.status-dot {
    width: 7px; height: 7px;
    background: #34d399; border-radius: 50%;
    display: inline-block;
    box-shadow: 0 0 6px rgba(52,211,153,0.5);
}

/* ===== CHAT BUBBLES ===== */
.msg-user {
    align-self: flex-end;
    background: linear-gradient(135deg, #6366f1, #4f46e5);
    color: white;
    padding: 0.6rem 0.95rem;
    border-radius: 14px 14px 4px 14px;
    max-width: 80%;
    font-size: 0.88rem;
    line-height: 1.5;
    word-wrap: break-word;
    margin-bottom: 0.35rem;
    box-shadow: 0 2px 8px rgba(99,102,241,0.2);
}
.msg-bot {
    align-self: flex-start;
    background: rgba(255,255,255,0.035);
    border: 1px solid rgba(255,255,255,0.06);
    color: #cbd5e1;
    padding: 0.6rem 0.95rem;
    border-radius: 14px 14px 14px 4px;
    max-width: 90%;
    font-size: 0.88rem;
    line-height: 1.5;
    word-wrap: break-word;
    margin-bottom: 0.35rem;
}
.msg-time {
    font-size: 0.66rem; color: #475569; margin-top: 0.15rem;
    font-weight: 500;
}

/* ===== INPUT ===== */
.stTextInput > div > div > input {
    background: rgba(255,255,255,0.035) !important;
    color: #f1f5f9 !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 10px !important;
    padding: 0.6rem 0.85rem !important;
    font-size: 0.88rem !important;
    font-family: 'Inter', sans-serif !important;
    transition: border-color 0.2s !important;
}
.stTextInput > div > div > input:focus {
    border-color: rgba(99,102,241,0.45) !important;
    box-shadow: 0 0 0 2px rgba(99,102,241,0.12) !important;
}
.stTextInput > div > div > input::placeholder {
    color: #475569 !important;
}

/* ===== BUTTONS ===== */
.stButton > button {
    background: #4f46e5;
    color: white; border: none; border-radius: 10px;
    padding: 0.48rem 0.95rem; font-weight: 600; font-size: 0.82rem;
    font-family: 'Inter', sans-serif;
    letter-spacing: 0.01em;
    transition: all 0.15s ease;
    box-shadow: 0 2px 8px rgba(79,70,229,0.2);
}
.stButton > button:hover {
    background: #4338ca;
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(79,70,229,0.3);
}

/* ===== KPI CARDS ===== */
.kpi-row { display: flex; gap: 0.7rem; margin-bottom: 0.9rem; flex-wrap: wrap; }
.kpi-card {
    flex: 1; min-width: 125px;
    background: rgba(255,255,255,0.025);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 12px;
    padding: 0.7rem 0.9rem;
    text-align: center;
    transition: border-color 0.2s;
}
.kpi-card:hover { border-color: rgba(99,102,241,0.25); }
.kpi-label {
    font-size: 0.7rem; color: #64748b;
    text-transform: uppercase; letter-spacing: 0.8px;
    font-weight: 600; margin-bottom: 0.2rem;
}
.kpi-value {
    font-size: 1.35rem; font-weight: 700; color: #f1f5f9;
    letter-spacing: -0.5px;
}

/* ===== SQL BLOCK ===== */
.sql-block {
    background: rgba(0,0,0,0.22);
    border: 1px solid rgba(255,255,255,0.05);
    border-radius: 10px;
    padding: 0.6rem 0.85rem;
    margin: 0.5rem 0;
    font-family: 'JetBrains Mono', 'Fira Code', monospace;
    font-size: 0.76rem;
    color: #818cf8;
    overflow-x: auto;
    white-space: pre-wrap;
    line-height: 1.6;
}

/* ===== INSIGHT BOX ===== */
.insight-box {
    background: rgba(52,211,153,0.05);
    border-left: 3px solid #34d399;
    border-radius: 0 10px 10px 0;
    padding: 0.6rem 0.95rem;
    margin: 0.5rem 0;
    font-size: 0.86rem;
    color: #a7f3d0;
    line-height: 1.55;
}

/* ===== BADGES ===== */
.badge-row { display: flex; gap: 0.35rem; flex-wrap: wrap; margin: 0.35rem 0; }
.badge {
    display: inline-flex; align-items: center; gap: 0.2rem;
    background: rgba(255,255,255,0.035);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 6px;
    padding: 0.2rem 0.5rem;
    font-size: 0.7rem;
    color: #94a3b8;
    font-weight: 500;
    letter-spacing: 0.02em;
}
.badge-green {
    background: rgba(52,211,153,0.07);
    border-color: rgba(52,211,153,0.18);
    color: #6ee7b7;
}

/* ===== DATA TABLE ===== */
div[data-testid="stDataFrame"] {
    border-radius: 10px; overflow: hidden;
    border: 1px solid rgba(255,255,255,0.05);
}
pre {
    border-radius: 10px !important;
    background: rgba(0,0,0,0.18) !important;
    font-family: 'JetBrains Mono', monospace !important;
}

/* ===== SIDEBAR ===== */
section[data-testid="stSidebar"] {
    background: rgba(10,14,28,0.97);
    border-right: 1px solid rgba(255,255,255,0.04);
}
section[data-testid="stSidebar"] .stButton > button {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.07);
    color: #cbd5e1;
    box-shadow: none;
    font-weight: 500;
    text-align: left;
    justify-content: flex-start;
}
section[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(99,102,241,0.1);
    border-color: rgba(99,102,241,0.22);
    color: #e2e8f0;
    transform: none;
    box-shadow: none;
}

/* ===== PLOTLY ===== */
.stPlotlyChart { border-radius: 12px; overflow: hidden; }

/* ===== SCROLLBAR ===== */
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.07); border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.12); }

/* ===== METRIC ===== */
div[data-testid="stMetric"] {
    background: rgba(255,255,255,0.025);
    border: 1px solid rgba(255,255,255,0.05);
    border-radius: 10px; padding: 0.7rem;
}
div[data-testid="stMetricValue"] { color: #f1f5f9; font-weight: 700; }
div[data-testid="stMetricLabel"] { color: #64748b; font-weight: 500; }

/* Hide streamlit extras */
div[data-testid="stDecoration"] { display: none; }
#MainMenu { visibility: hidden; }

/* ===== RESULT PANEL ===== */
.result-panel {
    background: rgba(255,255,255,0.015);
    border: 1px solid rgba(255,255,255,0.05);
    border-radius: 12px;
    padding: 0.9rem 1rem;
    margin-top: 0.5rem;
}

/* ===== EXPANDER ===== */
details[data-testid="stExpander"] {
    border: 1px solid rgba(255,255,255,0.05) !important;
    border-radius: 10px !important;
    background: rgba(255,255,255,0.015) !important;
}
details[data-testid="stExpander"] summary {
    font-weight: 500 !important;
    font-size: 0.82rem !important;
    color: #94a3b8 !important;
}

/* ===== HIGHLIGHT ITEMS ===== */
.highlight-item {
    font-size: 0.83rem;
    color: #94a3b8;
    padding: 0.12rem 0;
    line-height: 1.5;
}

/* ===== METRIC PILL ===== */
.metric-pill {
    background: rgba(255,255,255,0.025);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 12px;
    padding: 0.75rem 0.9rem;
    text-align: center;
    box-shadow: 0 2px 10px rgba(0,0,0,0.12);
}
.metric-label {
    color: #64748b;
    font-size: 0.8rem;
    font-weight: 500;
    margin-bottom: 0.2rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
.metric-value {
    color: #f1f5f9;
    font-size: 1.3rem;
    font-weight: 700;
    letter-spacing: -0.3px;
}

/* ===== SECTION HEADINGS ===== */
h4 {
    font-weight: 600 !important;
    letter-spacing: -0.3px !important;
    color: #e2e8f0 !important;
    font-size: 1.02rem !important;
}
</style>
""", unsafe_allow_html=True)