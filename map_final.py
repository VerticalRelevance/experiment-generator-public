map_actions = {
    "stop-provider-service": {
        "type": "action",
        "name": "stop-provider-service",
        "provider": {
            "type": "python",
            "module": "chaosk8s.actions",
            "func": "kill_microservice"
        },
        "pauses": {
            "after": 15
        }
    },
    "talk-to-webapp": {
        "type": "action",
        "name": "talk-to-webapp",
        "background": True,
        "provider": {
            "type": "process",
            "path": "vegeta",
            "timeout": 63,
            "arguments": {
                "attack": "",
                "-duration": "60s",
                "-connections": "1",
                "-rate": "1",
                "-output": "report.bin",
                "-targets": "urls.txt"
            }
        }
    },
    "confirm-purchase": {
        "type": "action",
        "name": "confirm-purchase",
        "provider": {
            "type": "http",
            "url": "${webapp_service_url}/purchase/confirm"
        },
        "pauses": {
            "before": 15
        }
    },
}

map_probes = {
    "all-services-are-healthy": {
        "type": "probe",
        "name": "all-services-are-healthy",
        "tolerance": True,
        "provider": {
            "type": "python",
            "module": "chaosk8s.probes",
            "func": "all_microservices_healthy"
        }
    },
    "consumer-service-must-still-respond": {
        "type": "probe",
        "name": "consumer-service-must-still-respond",
        "tolerance": 200,
        "provider": {
            "type": "http",
            "url": "http://192.168.39.7:31546/invokeConsumedService"
        }
    },
    "webapp-is-available" : {
        "type": "probe",
        "name": "webapp-is-available",
        "tolerance": True,
        "provider": {
            "type": "python",
            "module": "chaosk8s.probes",
            "func": "microservice_available_and_healthy",
            "arguments": {
                "name": "webapp-app"
            }
        }
    },
    "collect-how-many-times-our-service-container-restarted-in-the-last-minute":{
        "type": "probe",
        "name": "collect-how-many-times-our-service-container-restarted-in-the-last-minute",
        "provider": {
            "type": "python",
            "module": "chaosprometheus.probes",
            "func": "query_interval",
            "arguments": {
                "query": "kube_pod_container_status_restarts{container=\"webapp-app\"}",
                "start": "2 minutes ago",
                "end": "now"
            }
        },
        "pauses": {
            "before": 45
        }
    },
    "read-webapp-logs-for-the-pod-that-was-killed": {
        "type": "probe",
        "name": "read-webapp-logs-for-the-pod-that-was-killed",
        "provider": {
            "type": "python",
            "module": "chaosk8s.probes",
            "func": "read_microservices_logs",
            "arguments": {
                "name": "webapp-app",
                "from_previous": True
            }
        }
    },
    "read-webapp-logs-for-pod-that-was-started": {
        "type": "probe",
        "name": "read-webapp-logs-for-pod-that-was-started",
        "provider": {
            "type": "python",
            "module": "chaosk8s.probes",
            "func": "read_microservices_logs",
            "arguments": {
                "name": "webapp-app"
            }
        }
    },
    "collect-status-code-from-our-webapp-in-the-last-2-minutes": {
        "type": "probe",
        "name": "collect-status-code-from-our-webapp-in-the-last-2-minutes",
        "provider": {
            "type": "python",
            "module": "chaosprometheus.probes",
            "func": "query_interval",
            "arguments": {
                "query": "flask_http_request_duration_seconds_count{path=\"/\"}",
                "start": "2 minutes ago",
                "end": "now"
            }
        },
        "pauses": {
            "before": 10
        }
    },
    "plot-request-latency-throughout-experiment": {
        "type": "probe",
        "name": "plot-request-latency-throughout-experiment",
        "provider": {
            "type": "process",
            "path": "vegeta",
            "timeout": 5,
            "arguments": {
                "report": "",
                "-inputs": "report.bin",
                "-reporter": "plot",
                "-output": "latency.html"
            }
        },
        "pauses": {
            "before": 5
        }
    }
}