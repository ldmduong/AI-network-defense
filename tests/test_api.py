from pathlib import Path

import pandas as pd
from fastapi.testclient import TestClient

from app.main import app
from app.ml_engine import ml_engine


client = TestClient(app)

PROJECT_DIR = Path(__file__).resolve().parent.parent
TEST_DATA_PATH = (
    PROJECT_DIR
    / "data"
    / "splits"
    / "test.csv"
)


def create_valid_payload():
    dataframe = pd.read_csv(TEST_DATA_PATH)
    row = dataframe.iloc[0]

    return {
        feature: float(row[feature])
        for feature in ml_engine.feature_columns
    }


def test_root(): # khoi dong dung 
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["version"] == "0.1.0"


def test_health_check(): # health check point 
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_analyze_valid_flow(): # kiem tra tona bo model 
    payload = create_valid_payload()

    response = client.post(
        "/api/v1/analyze",
        json=payload,
    )

    assert response.status_code == 200

    result = response.json()

    assert "anomaly_score" in result
    assert "is_anomaly" in result
    assert "predicted_attack" in result
    assert "confidence" in result
    assert "attack_probabilities" in result
    assert "dqn_state" in result
    assert "action" in result
    assert "action_id" in result

    assert len(result["dqn_state"]) == 11
    assert result["action"] in ml_engine.actions
    assert result["action_id"] in range(len(ml_engine.actions))


def test_analyze_missing_data():
    response = client.post(
        "/api/v1/analyze",
        json={},
    )

    assert response.status_code == 422


def test_feedback():
    payload = {
        "predicted_attack": "Normal Traffic",
        "actual_attack": "Normal Traffic",
        "recommended_action": "ALLOW",
        "action_was_correct": True,
        "comment": "Test feedback",
    }

    response = client.post(
        "/api/v1/feedback",
        json=payload,
    )

    assert response.status_code == 200
    assert response.json()["status"] == "accepted"


def test_metrics():
    response = client.get("/api/v1/metrics")

    assert response.status_code == 200

    result = response.json()

    assert "analysis_requests" in result
    assert "feedback_requests" in result
    assert result["model_features"] == 52