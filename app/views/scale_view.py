import streamlit as st
from app.services.k8s_service import scale_deployment
from app.utils.state import go_to_main

def display_scale_view():
    st.title("Scaling Deployment")
    st.button("Back to Main", on_click=go_to_main)
    intent = st.session_state.response_json
    service = intent.get("service")
    replicas = intent.get("replicas")
    namespace = intent.get("namespace", "default")

    if service and replicas is not None:
        msg = scale_deployment(service, replicas, namespace)
        st.success(msg)
    else:
        st.warning("Could not determine service or replicas from the intent.")
    st.json(intent)