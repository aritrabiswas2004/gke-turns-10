import streamlit as st
import tempfile
import pandas as pd
import json
from dotenv import load_dotenv
from google import genai
from kubernetes import client, config
from kubernetes.client import ApiException

# from .env (DONT PUSH TO GITHUB)
load_dotenv()
API_KEY = st.secrets.get("API_KEY") # os.getenv("API_KEY")

if not API_KEY:
    st.error("API key not found...")
    st.stop()

kubeconfig_content = st.secrets.get("KUBECONFIG")

with tempfile.NamedTemporaryFile(delete=False) as tmp:
    tmp.write(kubeconfig_content.encode())
    tmp_path = tmp.name

# more from py client for k8s
# https://github.com/kubernetes-client/python
try:
    config.load_kube_config(config_file=tmp_path)
    v1 = client.CoreV1Api()
    apps_v1 = client.AppsV1Api()
except config.config_exception.ConfigException as e:
    st.error(f"Kubernetes configuration error: {e}")
    st.stop()

# Gemini client setup
gclient = genai.Client(api_key=API_KEY)

podnames = [
    "recommendationservice", "emailservice", "productcatalogservice",
    "adservice", "shippingservice", "frontend",
    "cartservice", "currencyservice", "paymentservice",
    "checkoutservice"
]


def initialize_session_state():
    if 'current_view' not in st.session_state:
        st.session_state.current_view = 'main'
    if 'service' not in st.session_state:
        st.session_state.service = None
    if 'logs' not in st.session_state:
        st.session_state.logs = None
    if 'response_json' not in st.session_state:
        st.session_state.response_json = None
    if 'description' not in st.session_state:
        st.session_state.description = None
    if 'prompt' not in st.session_state:
        st.session_state.prompt = None


initialize_session_state()


def get_pod_status(pod_name: str, namespace: str):
    try:
        pods = v1.list_namespaced_pod(namespace)
        for pod in pods.items:
            if pod_name in pod.metadata.name:
                return {
                    "Pod": pod.metadata.name,
                    "Status": pod.status.phase,
                    "Node": pod.spec.node_name,
                    "Restarts": sum([c.restart_count for c in pod.status.container_statuses or []]),
                }
        return {"Pod": pod_name, "Status": "NOT FOUND", "Node": "-", "Restarts": "-"}
    except ApiException as e:
        return {"Pod": pod_name, "Status": f"ERROR: {e.reason}", "Node": "-", "Restarts": "-"}


def color_status(val):
    if val == "Running":
        return "color: green;"
    elif val == "NOT FOUND":
        return "color: red;"
    elif val == "Pending":
        return "color:orange;"
    return ""


def describe_pod(pod_name: str, namespace="default"):
    try:
        pods = v1.list_namespaced_pod(namespace)

        for pod in pods.items:
            if pod_name in pod.metadata.name:
                return f"""
                
                === Metadata ===
                
                Pod Name: {pod.metadata.name}
                Namespace: {pod.metadata.namespace}
                Node: {pod.spec.node_name}
                Labels: {pod.metadata.labels}
                Annotations: {pod.metadata.annotations}
                
                === Status ===
                
                Host IP: {pod.status.host_ip}
                Pod IP: {pod.status.pod_ip}
                Container: {pod.status.container_statuses}
                """

        return f"No pod found for {pod_name}"
    except ApiException as e:
        return f"API ERROR:{e}"
    except Exception as x:
        return f"Some other error {x}"

def pod_description_with_gemini(description: str, service: str, prompt: str):
    desc_prompt = f"""
Given below is part of the description for a {service} pod running on my GKE cluster for an online boutique store application.

{description}

Based on the above description answer the prompt given (by another person) below. If not possible suggest ways and commands on how to resolve any issues in the prompt if it makes sense

{prompt}
"""
    response = gclient.models.generate_content(
        model="gemini-2.5-flash",
        contents=desc_prompt
    )
    return response.text

def get_logs(service: str, namespace="default", tail_lines=100):
    try:
        pods = v1.list_namespaced_pod(namespace)
        for pod in pods.items:
            if service in pod.metadata.name:
                return v1.read_namespaced_pod_log(
                    name=pod.metadata.name,
                    namespace=namespace,
                    tail_lines=tail_lines
                )
        return f"No pod found for {service}"
    except ApiException as e:
        return f"Error fetching logs for {service}: {e.reason}"


def scale_deployment(service: str, replicas: int, namespace="default"):
    try:
        body = {"spec": {"replicas": replicas}}
        apps_v1.patch_namespaced_deployment_scale(
            name=service, namespace=namespace, body=body
        )
        return f"Scaled {service} to {replicas} replicas."
    except ApiException as e:
        return f"Error scaling {service}: {e.reason}"

def get_gemini_intent(prompt: str):
    modified_prompt = f"""
    Convert this user request into JSON with fields:
    - action: one of [logs, scale, description, irrelevant, help]
    - service: the pod/deployment name, one of {podnames}
    - namespace: default unless specified
    - replicas: integer if scaling, else null

    Request: {prompt}
    Respond with only valid JSON and nothing else. Do not use markdown backticks.
    """
    response = gclient.models.generate_content(
        model="gemini-2.5-flash",
        contents=modified_prompt
    )
    try:
        return json.loads(response.text.strip())
    except (json.JSONDecodeError, AttributeError) as e:
        st.error(f"Could not parse Gemini response: {response.text}")
        return None


def analyze_logs_with_gemini(logs: str, service: str, prompt: str):
    modified_followup_prompt = f"""
    Given below are the logs for the {service} of my application.

    {logs}

    Based on the given logs for {service}, answer the prompt below in detail.

    User prompt: {prompt}

    For context, other services running are: {', '.join(podnames)}.
    """
    response = gclient.models.generate_content(
        model="gemini-2.5-flash",
        contents=modified_followup_prompt
    )
    return response.text

def go_to_main():
    st.session_state.current_view = 'main'
    st.session_state.service = None
    st.session_state.logs = None
    st.session_state.description = None
    st.session_state.response_json = None
    st.session_state.prompt = None
    st.rerun()


def process_main_prompt(prompt):
    with st.spinner("Analyzing prompt with Gemini..."):
        intent = get_gemini_intent(prompt)
        if intent:
            st.session_state.response_json = intent
            action = intent.get("action")
            service = intent.get("service")

            if action == "logs":
                st.session_state.service = service
                st.session_state.logs = get_logs(service, intent.get("namespace", "default"))
                st.session_state.current_view = 'logs_view'
            elif action == "scale":
                st.session_state.current_view = 'scale_view'
            elif action == "status":
                st.session_state.current_view = 'status_view'
            elif action == "irrelevant":
                st.session_state.current_view = 'irrelevant_view'
            elif action == "description":
                st.session_state.prompt = prompt
                st.session_state.service = service
                st.session_state.description = describe_pod(service, intent.get("namespace", "default"))
                st.session_state.current_view = 'description_view'
            elif action == "help":
                st.session_state.current_view = 'help_view'
            else:
                st.warning("Unknown action")

        st.rerun()


def display_main_view():
    st.title("Gemini Cluster Assistant for Kubernetes")
    pod_data = [get_pod_status(name, "default") for name in podnames]
    df = pd.DataFrame(pod_data)
    st.dataframe(df.style.map(color_status, subset=["Status"]))

    with st.form("main_form"):
        prompt = st.text_area("Enter a prompt...", height=120)
        submitted = st.form_submit_button("Send to Gemini")

    if submitted and prompt.strip():
        process_main_prompt(prompt)


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

def display_irrelevant_view():
    st.title(f"Irrelevant Prompt")
    st.write("Looks like you asked an irrelevant prompt to this k8s cluster-specific Gemini agent. Click on the button below to go back to the home page and try again")
    st.button("Back to Home (main Gemini Prompt)", on_click=go_to_main)


def display_description_view():
    st.title(f"Describing {st.session_state.service} Pod")
    st.button("Back to Home (main Gemini Prompt)", on_click=go_to_main)

    # debug only
    # st.text_area(f"Logs for {st.session_state.service}", st.session_state.description, height=200)

    with st.spinner("Reviewing the Pod Description..."):
        response = pod_description_with_gemini(
            st.session_state.description, st.session_state.service, st.session_state.prompt
        )
        st.subheader("Gemini's Answer:")
        st.markdown(response)

def display_help_view():
    st.title("Help for this Application")
    st.button("Back to Home (main Gemini Prompt)", on_click=go_to_main)

    st.markdown("""
> NOTE: This help message is not generated by Gemini
                
## Help Areas
                
This Gemini Cluster Assistant can help you in the following areas.
                
### Get Pod-level Description
                
- Get all metadata for a Pod
- Get which node is controlling the pod
- Get which containers are running in the pod
- Get resource limits and usage information
                
### Get and Analyze Logs
                
- Fetch logs from a particular pod
- Analyze the logs further with Gemini for Error Reports, Pod status, Failed transactions etc.

### Scale Deployments
                
- You can scale up or down the replicas in a deployment.

""")

if st.session_state.current_view == 'main':
    display_main_view()
elif st.session_state.current_view == 'logs_view':
    display_logs_view()
elif st.session_state.current_view == 'scale_view':
    display_scale_view()
elif st.session_state.current_view == 'status_view':
    display_status_view()
elif st.session_state.current_view == 'irrelevant_view':
    display_irrelevant_view()
elif st.session_state.current_view == 'description_view':
    display_description_view()
elif st.session_state.current_view == 'help_view':
    display_help_view()
