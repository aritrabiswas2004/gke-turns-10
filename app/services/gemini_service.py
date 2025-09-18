import os, json, streamlit as st
from dotenv import load_dotenv
from google import genai

load_dotenv()
API_KEY = os.getenv("API_KEY")
if not API_KEY:
    st.error("API key not found.")
    st.stop()

gclient = genai.Client(api_key=API_KEY)

PODNAMES = [
    "recommendationservice","emailservice","productcatalogservice",
    "adservice","shippingservice","frontend",
    "cartservice","currencyservice","paymentservice","checkoutservice"
]

def get_gemini_intent(prompt: str):
    modified_prompt = f"""
    Convert this user request into JSON with fields:
    - action: one of [status, logs, scale]
    - service: the pod/deployment name, one of {PODNAMES}
    - namespace: default unless specified
    - replicas: integer if scaling, else null

    Request: {prompt}
    Respond with only valid JSON and nothing else. Do not use markdown syntax or any markdown backticks.
    """
    response = gclient.models.generate_content(
        model="gemini-2.5-flash", contents=modified_prompt
    )
    try:
        return json.loads(response.text.strip())
    except (json.JSONDecodeError, AttributeError):
        st.error(f"Could not parse Gemini response: {response.text}")
        return None

def analyze_logs_with_gemini(logs: str, service: str, prompt: str):
    followup = f"""
    Logs for {service}:

    {logs}

    User prompt: {prompt}
    """
    resp = gclient.models.generate_content(
        model="gemini-2.5-flash", contents=followup
    )
    return resp.text
