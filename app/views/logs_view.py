import streamlit as st
from ..services.gemini_service import analyze_logs_with_gemini
from ..utils.state import go_to_main

def display_logs_view():
    st.title(f"Logs for {st.session_state.service}")
    st.button("Back to Home (main Gemini Prompt)", on_click=go_to_main)
    st.text_area(f"Logs for {st.session_state.service}", st.session_state.logs, height=200)

    with st.form("followup_form"):
        followup_prompt = st.text_area("Ask a question about the logs...", height=120)
        followup_submitted = st.form_submit_button("Analyze with Gemini")

    if followup_submitted and followup_prompt.strip():
        with st.spinner("Analyzing..."):
            response = analyze_logs_with_gemini(
                st.session_state.logs, st.session_state.service, followup_prompt
            )
            st.subheader("Gemini's Answer:")
            st.markdown(response)
