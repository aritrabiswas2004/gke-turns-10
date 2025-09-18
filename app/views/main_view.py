import streamlit as st
import pandas as pd
from app.services.k8s_service import get_pod_status
from app.services.gemini_service import PODNAMES, get_gemini_intent

def color_status(val):
    return "color: green;" if val == "Running" else \
           "color: red;"   if val == "NOT FOUND" else \
           "color: orange;" if val == "Pending" else ""

def process_main_prompt(prompt):
    with st.spinner("Analyzing prompt with Gemini..."):
        intent = get_gemini_intent(prompt)
        if not intent:
            return
        st.session_state.response_json = intent
        action = intent.get("action")
        service = intent.get("service")

        if action == "logs":
            from app.services.k8s_service import get_logs
            st.session_state.service = service
            st.session_state.logs = get_logs(service, intent.get("namespace", "default"))
            st.session_state.current_view = "logs_view"
        elif action == "scale":
            st.session_state.current_view = "scale_view"
        elif action == "status":
            st.session_state.current_view = "status_view"
        else:
            st.warning("Unknown action")
        st.rerun()

def display_main_view():
    st.title("Gemini Cluster Assistant for Kubernetes")
    df = pd.DataFrame([get_pod_status(n, "default") for n in PODNAMES])
    st.dataframe(df.style.map(color_status, subset=["Status"]))

    with st.form("main_form"):
        prompt = st.text_area("Enter a prompt...", height=120)
        if st.form_submit_button("Send to Gemini") and prompt.strip():
            process_main_prompt(prompt)
