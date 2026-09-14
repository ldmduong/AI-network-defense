from pathlib import Path
import json

import mlflow


PROJECT_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = PROJECT_DIR / "models"
MLFLOW_DB_PATH = PROJECT_DIR / "mlflow.db"


mlflow.set_tracking_uri(
    "sqlite:///" + MLFLOW_DB_PATH.as_posix()
)

mlflow.set_experiment("ai-network-defense")


with open(
    MODELS_DIR / "anomaly_threshold.json",
    "r",
    encoding="utf-8",
) as file:
    autoencoder_metadata = json.load(file)


with mlflow.start_run(run_name="autoencoder"):
    mlflow.log_param(
        "model_type",
        "Autoencoder",
    )

    mlflow.log_param(
        "feature_count",
        len(autoencoder_metadata["feature_columns"]),
    )

    mlflow.log_metric(
        "threshold",
        autoencoder_metadata["threshold"],
    )

    mlflow.log_metric(
        "test_fpr",
        autoencoder_metadata["test_fpr"],
    )

    mlflow.log_metric(
        "test_recall",
        autoencoder_metadata["test_recall"],
    )

    mlflow.log_metric(
        "test_precision",
        autoencoder_metadata["test_precision"],
    )

    mlflow.log_metric(
        "test_f1",
        autoencoder_metadata["test_f1"],
    )

    mlflow.log_artifact(
        str(MODELS_DIR / "anomaly_threshold.json")
    )

    mlflow.log_artifact(
        str(MODELS_DIR / "autoencoder_full.pt")
    )

    mlflow.log_artifact(
        str(MODELS_DIR / "autoencoder_scaler.joblib")
    )



with open(
    MODELS_DIR / "xgboost_metadata.json",
    "r",
    encoding="utf-8",
) as file:
    xgboost_metadata = json.load(file)


with mlflow.start_run(run_name="xgboost"):
    mlflow.log_param(
        "model_type",
        xgboost_metadata["model_type"],
    )

    mlflow.log_param(
        "target",
        xgboost_metadata["target"],
    )

    mlflow.log_param(
        "feature_count",
        len(xgboost_metadata["feature_columns"]),
    )

    mlflow.log_param(
        "class_count",
        len(xgboost_metadata["classes"]),
    )

    mlflow.log_metric(
        "test_accuracy",
        xgboost_metadata["test_accuracy"],
    )

    mlflow.log_metric(
        "test_macro_f1",
        xgboost_metadata["test_macro_f1"],
    )

    mlflow.log_metric(
        "test_weighted_f1",
        xgboost_metadata["test_weighted_f1"],
    )

    mlflow.log_metric(
        "best_iteration",
        xgboost_metadata["best_iteration"],
    )

    mlflow.log_artifact(
        str(MODELS_DIR / "xgboost_classifier.json")
    )

    mlflow.log_artifact(
        str(MODELS_DIR / "xgboost_label_encoder.joblib")
    )

    mlflow.log_artifact(
        str(MODELS_DIR / "xgboost_metadata.json")
    )
with open(
    MODELS_DIR / "dqn_policy_v2_metadata.json",
    "r",
    encoding="utf-8",
) as file:
    dqn_metadata = json.load(file)


dqn_evaluation = dqn_metadata["held_out_evaluation"]
dqn_defense_metrics = dqn_evaluation["defense_metrics"]


with mlflow.start_run(run_name="dqn-v2"):
    mlflow.log_param(
        "model_type",
        dqn_metadata["model_type"],
    )

    mlflow.log_param(
        "version",
        dqn_metadata["version"],
    )

    mlflow.log_param(
        "state_size",
        dqn_metadata["state_size"],
    )

    mlflow.log_param(
        "action_count",
        len(dqn_metadata["actions"]),
    )

    mlflow.log_param(
        "training_timesteps",
        dqn_metadata["training"]["training_timesteps"],
    )

    mlflow.log_metric(
        "average_reward",
        dqn_evaluation["average_reward"],
    )

    mlflow.log_metric(
        "total_reward",
        dqn_evaluation["total_reward"],
    )

    mlflow.log_metric(
        "missed_attack_rate",
        dqn_defense_metrics["missed_attack_rate"],
    )

    mlflow.log_metric(
        "false_mitigation_rate",
        dqn_defense_metrics["false_mitigation_rate"],
    )

    mlflow.log_metric(
        "block_rate_on_attack",
        dqn_defense_metrics["block_rate_on_attack"],
    )

    mlflow.log_metric(
        "escalation_rate",
        dqn_defense_metrics["escalation_rate"],
    )

    mlflow.log_artifact(
        str(MODELS_DIR / "dqn_policy_v2.zip")
    )

    mlflow.log_artifact(
        str(MODELS_DIR / "dqn_policy_v2_metadata.json")
    )

print("DQN v2 run logged successfully")
print("XGBoost run logged successfully")
print("Autoencoder run logged successfully")