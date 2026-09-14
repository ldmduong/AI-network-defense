from fastapi import FastAPI, HTTPException

from app.ml_engine import ml_engine
from app.schema import FeedbackRequest, NetworkFlowRequest

import time

from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from app.metrics import (
    ANALYZE_ERRORS,
    ANALYZE_REQUESTS,
    ATTACK_PREDICTIONS,
    INFERENCE_LATENCY,
    RESPONSE_ACTIONS,
)


analysis_count = 0
feedback_count = 0




app = FastAPI(
    title="AI Network Defense API",
    description="API for network intrusion detection and autonomous response",
    version="0.1.0",
)


@app.get("/")
def read_root():
    return {
        "message": "AI Network Defense API is running",
        "version": "0.1.0",
    }


@app.get("/api/v1/health")
def health_check():
    return {
        "status": "ok",
        "service": "network-defense-api",
    }


@app.post("/api/v1/analyze")
def analyze_flow(request: NetworkFlowRequest):
    start_time = time.perf_counter()
    ANALYZE_REQUESTS.inc()

    flow = request.model_dump(by_alias=True)

    try:
        result = ml_engine.analyze_flow(flow)

        ATTACK_PREDICTIONS.labels(
            attack_type=result["predicted_attack"]
        ).inc()

        RESPONSE_ACTIONS.labels(
            action=result["action"]
        ).inc()

        return result

    except (TypeError, ValueError):
        ANALYZE_ERRORS.inc()
        raise

    finally:
        elapsed_time = time.perf_counter() - start_time
        INFERENCE_LATENCY.observe(elapsed_time)


@app.post("/api/v1/feedback")
def submit_feedback(feedback: FeedbackRequest):
    global feedback_count
    feedback_count += 1

    return {
        "status": "accepted",
        "message": (
            "Feedback received. It can be used for a future retraining job."
        ),
        "feedback_number": feedback_count,
        "feedback": feedback.model_dump(),
    }


@app.get("/api/v1/metrics")
def get_metrics():
    return {
        "analysis_requests": analysis_count,
        "feedback_requests": feedback_count,
        "model_device": str(ml_engine.device),
        "model_features": len(ml_engine.feature_columns),
        "dqn_actions": ml_engine.actions,
    }

@app.get("/metrics")
def metrics():
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )