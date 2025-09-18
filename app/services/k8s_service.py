from kubernetes import client, config
from kubernetes.client import ApiException

config.load_kube_config()
v1 = client.CoreV1Api()
apps_v1 = client.AppsV1Api()

def get_pod_status(pod_name: str, namespace="default"):
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



