import streamlit as st
from utils.state import initialize_session_state
from views.main_view import display_main_view
from views.logs_view import display_logs_view
from views.scale_view import display_scale_view
from views.status_view import display_status_view

initialize_session_state()

if st.session_state.current_view == "main":
    display_main_view()
elif st.session_state.current_view == "logs_view":
    display_logs_view()
elif st.session_state.current_view == "scale_view":
    display_scale_view()
elif st.session_state.current_view == "status_view":
    display_status_view()
