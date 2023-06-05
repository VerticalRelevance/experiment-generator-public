probe_mid_maps = {
    "webapp steady state": [
        "all-services-are-healthy",
        "webapp-is-available"
    ],
    "webapp restart-kubernetes": [
        "collect-how-many-times-our-service-container-restarted-in-the-last-minute",
        "read-webapp-logs-for-the-pod-that-was-killed",
        "read-webapp-logs-for-pod-that-was-started",
        "collect-status-code-from-our-webapp-in-the-last-2-minutes",
        "plot-request-latency-throughout-experiment"
    ]
}

actions_mid_maps = {
    "webapp restart-kubernetes": [
        "talk-to-webapp",
        "confirm-purchase"
    ]
}