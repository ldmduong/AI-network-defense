from prometheus_client import Counter, Histogram


ANALYZE_REQUESTS = Counter(
    "network_defense_analyze_requests_total",
    "Total number of analyze requests",
)

ANALYZE_ERRORS = Counter(
    "network_defense_analyze_errors_total",
    "Total number of analyze request errors",
)

INFERENCE_LATENCY = Histogram(
    "network_defense_inference_latency_seconds",
    "Inference latency in seconds",
)

ATTACK_PREDICTIONS = Counter(
    "network_defense_attack_predictions_total",
    "Number of predictions by attack type",
    ["attack_type"],
)

RESPONSE_ACTIONS = Counter(
    "network_defense_response_actions_total",
    "Number of response actions selected by DQN",
    ["action"],
)