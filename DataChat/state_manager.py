import streamlit as st


DEFAULT_TABLE = "claims"


def init_session_state():
    defaults = {
        "active_table": DEFAULT_TABLE,
        "last_plan": None,
        "last_question": None,
        "last_sql": None,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def get_active_table():
    return st.session_state.get("active_table", DEFAULT_TABLE)


def set_active_table(table_name):
    st.session_state["active_table"] = table_name


def get_last_plan():
    return st.session_state.get("last_plan")


def set_last_plan(plan):
    st.session_state["last_plan"] = plan


def get_last_question():
    return st.session_state.get("last_question")


def set_last_question(question):
    st.session_state["last_question"] = question


def get_last_sql():
    return st.session_state.get("last_sql")


def set_last_sql(sql):
    st.session_state["last_sql"] = sql


def clear_followup_context():
    st.session_state["last_plan"] = None
    st.session_state["last_question"] = None
    st.session_state["last_sql"] = None