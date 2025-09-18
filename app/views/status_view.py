import streamlit as st
from app.services.k8s_service import get_pod_status
from app.utils.state import go_to_main


def display_status_view():
    st.title("Service Status")
    st.button("Back to Main", on_click=go_to_main)
    intent = st.session_state.response_json
    service = intent.get("service")
    namespace = intent.get("namespace", "default")

    if service:
        status = get_pod_status(service, namespace)
        st.json(status)
    else:
        st.warning("Could not determine service from the intent.")
    st.json(intent)