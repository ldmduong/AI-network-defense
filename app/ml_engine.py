from pathlib import Path
import json

import joblib
import numpy as np
import pandas as pd
import torch
from stable_baselines3 import DQN
from torch import nn
from xgboost import XGBClassifier


PROJECT_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = PROJECT_DIR / "models"


class Autoencoder(nn.Module):
    def __init__(self, input_dim: int):
        super().__init__()

        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 32),
            nn.ReLU(),
            nn.Linear(32, 16),
            nn.ReLU(),
            nn.Linear(16, 8),
        )

        self.decoder = nn.Sequential(
            nn.Linear(8, 16),
            nn.ReLU(),
            nn.Linear(16, 32),
            nn.ReLU(),
            nn.Linear(32, input_dim),
        )

    def forward(self, x):
        latent = self.encoder(x)
        reconstructed = self.decoder(latent)
        return reconstructed


class MLEngine:
    def __init__(self):
        self.device = torch.device(
            "cuda" if torch.cuda.is_available() else "cpu"
        )

        self._load_autoencoder()
        self._load_xgboost()
        self._load_dqn()

    def _load_autoencoder(self):
        checkpoint_path = MODELS_DIR / "autoencoder_full.pt"

        checkpoint = torch.load(
            checkpoint_path,
            map_location=self.device,
            weights_only=False,
        )

        self.autoencoder = Autoencoder(
            input_dim=checkpoint["input_dim"]
        ).to(self.device)

        self.autoencoder.load_state_dict(
            checkpoint["model_state_dict"]
        )

        self.autoencoder.eval()

        self.scaler = joblib.load(
            MODELS_DIR / "autoencoder_scaler.joblib"
        )

        with open(
            MODELS_DIR / "anomaly_threshold.json",
            "r",
            encoding="utf-8",
        ) as file:
            metadata = json.load(file)

        self.anomaly_threshold = metadata["threshold"]
        self.feature_columns = metadata["feature_columns"]

    def _load_xgboost(self):
        self.xgb_model = XGBClassifier()

        self.xgb_model.load_model(
            MODELS_DIR / "xgboost_classifier.json"
        )

        self.label_encoder = joblib.load(
            MODELS_DIR / "xgboost_label_encoder.joblib"
        )

    def _load_dqn(self):
        dqn_model_path = MODELS_DIR / "dqn_policy_v2.zip"
        dqn_metadata_path = (
            MODELS_DIR / "dqn_policy_v2_metadata.json"
        )

        self.dqn_model = DQN.load(
            str(dqn_model_path),
            device=str(self.device),
        )

        with open(
            dqn_metadata_path,
            "r",
            encoding="utf-8",
        ) as file:
            metadata = json.load(file)

        self.actions = metadata["actions"]
        self.action_to_id = metadata["action_to_id"]
        self.id_to_action = {
            int(action_id): action_name
            for action_name, action_id in self.action_to_id.items()
        }
        self.dqn_state_size = metadata["state_size"]

    def _build_dqn_state(
        self,
        detection_result: dict,
        previous_action: str = "ALLOW",
        recent_alert_density: float = 0.0,
        action_cooldown: float = 0.0,
    ) -> np.ndarray:
        anomaly_score = float(
            detection_result["anomaly_score"]
        )

        anomaly_score_normalized = np.clip(
            np.log1p(anomaly_score)
            / np.log1p(100.0),
            0.0,
            1.0,
        )

        attack_probabilities = np.array(
            [
                detection_result["attack_probabilities"][label]
                for label in self.label_encoder.classes_
            ],
            dtype=np.float32,
        )

        if previous_action not in self.action_to_id:
            raise ValueError(
                f"Unknown previous action: {previous_action}"
            )

        previous_action_id = self.action_to_id[previous_action]
        previous_action_normalized = (
            previous_action_id / (len(self.actions) - 1)
        )

        state = np.concatenate(
            [
                np.array(
                    [anomaly_score_normalized],
                    dtype=np.float32,
                ),
                attack_probabilities,
                np.array(
                    [
                        previous_action_normalized,
                        recent_alert_density,
                        action_cooldown,
                    ],
                    dtype=np.float32,
                ),
            ]
        )

        if state.shape != (self.dqn_state_size,):
            raise ValueError(
                f"Invalid DQN state shape: {state.shape}"
            )

        return state

    def analyze_flow(self, flow: dict) -> dict:
        flow_df = pd.DataFrame(
            [flow],
            columns=self.feature_columns,
        )

        missing_columns = [
            column
            for column in self.feature_columns
            if column not in flow
        ]

        if missing_columns:
            raise ValueError(
                f"Missing feature columns: {missing_columns}"
            )

        x_raw = flow_df[self.feature_columns]

        x_scaled = self.scaler.transform(
            x_raw
        ).astype("float32")

        x_tensor = torch.tensor(
            x_scaled,
            dtype=torch.float32,
            device=self.device,
        )

        with torch.no_grad():
            reconstructed = self.autoencoder(x_tensor)

        anomaly_score = torch.mean(
            (x_tensor - reconstructed) ** 2,
            dim=1,
        ).item()

        is_anomaly = (
            anomaly_score > self.anomaly_threshold
        )

        predicted_id = int(
            self.xgb_model.predict(x_raw)[0]
        )

        probabilities = (
            self.xgb_model.predict_proba(x_raw)[0]
        )

        predicted_label = self.label_encoder.inverse_transform(
            [predicted_id]
        )[0]

        attack_probabilities = {
            label: float(probability)
            for label, probability in zip(
                self.label_encoder.classes_,
                probabilities,
            )
        }

        detection_result = {
            "anomaly_score": float(anomaly_score),
            "is_anomaly": bool(is_anomaly),
            "predicted_attack": str(predicted_label),
            "confidence": float(
                probabilities[predicted_id]
            ),
            "attack_probabilities": attack_probabilities,
        }

        dqn_state = self._build_dqn_state(
            detection_result=detection_result,
        )

        action_id, _ = self.dqn_model.predict(
            dqn_state,
            deterministic=True,
        )
        action_id = int(action_id)

        if action_id not in self.id_to_action:
            raise ValueError(
                f"Unknown DQN action ID: {action_id}"
            )

        return {
            **detection_result,
            "dqn_state": dqn_state.tolist(),
            "action": self.id_to_action[action_id],
            "action_id": action_id,
        }


ml_engine = MLEngine()