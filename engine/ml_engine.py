"""ByteShield - Module 4: Multi-Model Tabular & Isolation Forest ML Engine
Evaluates transaction velocity, geo-telemetry, amount deviation, and multi-factor
anomalies with high throughput and low false positive rate.
"""

import numpy as np
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from typing import Dict, Any, List


class MLEngine:
    """Hybrid Machine Learning & Anomaly Detection Engine for UPI Transactions."""

    def __init__(self):
        self.rf_classifier = None
        self.isolation_forest = None
        self.feature_names = [
            "amount",
            "amount_ratio",
            "account_age_hours",
            "vpa_similarity_score",
            "social_risk_score",
            "graph_risk_score",
            "hour_of_day",
            "is_collect_request",
            "is_new_device",
            "geo_distance_km"
        ]
        self._train_initial_models()

    def _train_initial_models(self):
        """Train models on synthetic UPI fraud & legitimate transaction baseline."""
        np.random.seed(42)
        n_legit = 1500
        n_fraud = 400

        # Legitimate transactions
        legit_amount = np.random.exponential(scale=1500, size=n_legit) + 50
        legit_ratio = np.random.uniform(0.1, 2.5, size=n_legit)
        legit_age = np.random.uniform(200, 10000, size=n_legit)
        legit_vpa_sim = np.random.uniform(0.0, 0.3, size=n_legit)
        legit_social = np.random.uniform(0, 15, size=n_legit)
        legit_graph = np.random.uniform(0, 10, size=n_legit)
        legit_hour = np.random.choice(range(8, 23), size=n_legit)
        legit_collect = np.random.choice([0, 1], p=[0.95, 0.05], size=n_legit)
        legit_device = np.random.choice([0, 1], p=[0.92, 0.08], size=n_legit)
        legit_geo = np.random.exponential(scale=15, size=n_legit)

        X_legit = np.column_stack([
            legit_amount, legit_ratio, legit_age, legit_vpa_sim,
            legit_social, legit_graph, legit_hour, legit_collect,
            legit_device, legit_geo
        ])
        y_legit = np.zeros(n_legit)

        # Fraudulent transactions
        fraud_amount = np.random.uniform(15000, 95000, size=n_fraud)
        fraud_ratio = np.random.uniform(4.0, 30.0, size=n_fraud)
        fraud_age = np.random.exponential(scale=8, size=n_fraud) + 0.5
        fraud_vpa_sim = np.random.uniform(0.7, 0.98, size=n_fraud)
        fraud_social = np.random.uniform(70, 100, size=n_fraud)
        fraud_graph = np.random.uniform(75, 100, size=n_fraud)
        fraud_hour = np.random.choice([1, 2, 3, 4, 14, 15, 23], size=n_fraud)
        fraud_collect = np.random.choice([0, 1], p=[0.5, 0.5], size=n_fraud)
        fraud_device = np.random.choice([0, 1], p=[0.3, 0.7], size=n_fraud)
        fraud_geo = np.random.uniform(500, 1800, size=n_fraud)

        X_fraud = np.column_stack([
            fraud_amount, fraud_ratio, fraud_age, fraud_vpa_sim,
            fraud_social, fraud_graph, fraud_hour, fraud_collect,
            fraud_device, fraud_geo
        ])
        y_fraud = np.ones(n_fraud)

        X = np.vstack([X_legit, X_fraud])
        y = np.concatenate([y_legit, y_fraud])

        self.rf_classifier = RandomForestClassifier(
            n_estimators=60,
            max_depth=8,
            random_state=42,
            n_jobs=-1
        )
        self.rf_classifier.fit(X, y)

        self.isolation_forest = IsolationForest(
            n_estimators=50,
            contamination=0.18,
            random_state=42
        )
        self.isolation_forest.fit(X_legit)

    def predict_risk(
        self,
        amount: float,
        sender_baseline_avg: float,
        account_age_hours: float,
        vpa_similarity_score: float,
        social_risk_score: float,
        graph_risk_score: float,
        hour_of_day: int,
        is_collect_request: bool,
        is_new_device: bool,
        geo_distance_km: float
    ) -> Dict[str, Any]:
        """
        Run multi-model prediction on transaction telemetry.
        """
        amount_ratio = (amount / sender_baseline_avg) if sender_baseline_avg > 0 else 1.0
        
        feature_vector = np.array([[
            amount,
            amount_ratio,
            account_age_hours,
            vpa_similarity_score,
            social_risk_score,
            graph_risk_score,
            float(hour_of_day),
            1.0 if is_collect_request else 0.0,
            1.0 if is_new_device else 0.0,
            geo_distance_km
        ]])

        rf_prob = float(self.rf_classifier.predict_proba(feature_vector)[0][1])
        iso_score = float(self.isolation_forest.decision_function(feature_vector)[0])
        iso_anomaly_prob = float(1.0 / (1.0 + np.exp(iso_score * 4.0)))

        blended_prob = (rf_prob * 0.70) + (iso_anomaly_prob * 0.30)
        ml_risk_score = int(np.clip(blended_prob * 100, 0, 100))

        # False Positive Suppression Filter
        if account_age_hours > 4000 and social_risk_score < 20 and vpa_similarity_score < 0.3 and graph_risk_score < 20:
            if ml_risk_score > 35:
                ml_risk_score = 15

        return {
            "ml_risk_score": ml_risk_score,
            "rf_probability": round(rf_prob, 4),
            "anomaly_score": round(iso_anomaly_prob, 4),
            "amount_ratio": round(amount_ratio, 2),
            "feature_vector": {
                name: float(val) for name, val in zip(self.feature_names, feature_vector[0])
            }
        }


ml_engine_instance = MLEngine()
