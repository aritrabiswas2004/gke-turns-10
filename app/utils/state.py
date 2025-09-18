import streamlit as st

def initialize_session_state():
    for key, value in {
        "current_view": "main",
        "service": None,
        "logs": None,
        "response_json": None,
    }.items():
        if key not in st.session_state:
            st.session_state[key] = value

def go_to_main():
    st.session_state.current_view = "main"
    st.session_state.service = None
    st.session_state.logs = None
    st.session_state.response_json = None
    st.rerun()
