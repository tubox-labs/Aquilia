"""
Auth ML Pipelines
=================

Scikit-learn powered ML pipelines for the auth module, registered with
Aquilia's MLOps subsystem via the ``@model`` decorator.

Four models cover the core security use-cases:

* **LoginRiskClassifier**   – score each login attempt (low / medium / high risk)
* **AnomalyDetector**       – isolate anomalous session / auth patterns
* **BruteForceDetector**    – online-learning detector for brute-force attacks
* **UserBehaviorClassifier**– cluster & classify long-term user behaviour

All pipelines are self-contained: they can be trained on synthetic data via
``warm_start()`` and then used immediately; or you can call ``fit()`` on real
data later. No external model files are required at boot.
"""

from __future__ import annotations

import logging
import pickle
import time
from typing import Any, Dict, List, Optional

import numpy as np
from sklearn.ensemble import (
    GradientBoostingClassifier,
    IsolationForest,
    RandomForestClassifier,
)
from sklearn.linear_model import LogisticRegression, SGDClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder

from aquilia.mlops import AquiliaModel, model

logger = logging.getLogger("myapp.auth.pipelines")

# ─────────────────────────────────────────────────────────────────────────────
# Shared helpers
# ─────────────────────────────────────────────────────────────────────────────

RISK_LABELS: List[str] = ["low", "medium", "high"]
BEHAVIOR_LABELS: List[str] = ["normal", "suspicious", "bot", "compromised"]

_HOUR_OF_DAY_BINS = list(range(25))  # 0..24 for boundary encoding


def _hour_bucket(hour: int) -> str:
    """Map hour-of-day to a named bucket (business / off-peak / night)."""
    if 8 <= hour < 18:
        return "business"
    if 18 <= hour < 23:
        return "evening"
    return "night"


def _ip_to_entropy(ip: str) -> float:
    """Rough proxy for IP 'surprise' – higher means rarer octets."""
    try:
        octets = [int(o) for o in ip.split(".")]
        # Private ranges have low entropy (expected), public ranges higher
        if octets[0] in (10, 127) or (octets[0] == 172 and 16 <= octets[1] <= 31):
            return 0.1
        if octets[0] == 192 and octets[1] == 168:
            return 0.1
        return round(sum(o / 255.0 for o in octets) / 4, 4)
    except Exception:
        return 0.5


# ─────────────────────────────────────────────────────────────────────────────
# 1. LoginRiskClassifier
# ─────────────────────────────────────────────────────────────────────────────

@model(
    name="login_risk_classifier",
    version="v1",
    device="cpu",
    batch_size=64,
    timeout_ms=5000.0,
    tags=["auth", "security", "classification", "sklearn"],
)
class LoginRiskClassifier(AquiliaModel):
    """
    Scores each login attempt as *low*, *medium*, or *high* risk.

    Input features
    --------------
    ``failed_attempts``     – int,   number of recent failures (last 15 min)
    ``ip_entropy``          – float, IP address surprise score 0..1
    ``hour_of_day``         – int,   0..23
    ``new_device``          – bool,  first time this device is seen
    ``vpn_proxy``           – bool,  IP is a known VPN / proxy
    ``geo_distance_km``     – float, distance from usual location
    ``time_since_last_ok``  – float, seconds since last successful login

    Output
    ------
    ``risk_label``   – str, one of "low" / "medium" / "high"
    ``risk_score``   – float, model probability of the predicted class
    ``probabilities``– dict, label → probability mapping
    """

    FEATURE_NAMES = [
        "failed_attempts",
        "ip_entropy",
        "hour_of_day",
        "new_device",
        "vpn_proxy",
        "geo_distance_km",
        "time_since_last_ok",
    ]

    def __init__(self) -> None:
        self._pipeline: Optional[Pipeline] = None
        self._label_encoder = LabelEncoder()
        self._is_fitted = False

    async def load(self, artifacts_dir: str, device: str) -> None:
        """Build and warm-start the pipeline with synthetic data."""
        self._pipeline = Pipeline([
            ("scaler", StandardScaler()),
            ("clf", RandomForestClassifier(
                n_estimators=120,
                max_depth=8,
                min_samples_split=5,
                class_weight="balanced",
                random_state=42,
                n_jobs=-1,
            )),
        ])
        self._warm_start()
        logger.info("LoginRiskClassifier loaded and warm-started.")

    def _warm_start(self) -> None:
        """Train on synthetic data so the model is immediately usable."""
        rng = np.random.default_rng(42)
        n = 3_000

        # Synthetic feature matrix
        X = np.column_stack([
            rng.integers(0, 20, n),          # failed_attempts
            rng.uniform(0, 1, n),            # ip_entropy
            rng.integers(0, 24, n),          # hour_of_day
            rng.integers(0, 2, n),           # new_device
            rng.integers(0, 2, n),           # vpn_proxy
            rng.uniform(0, 20_000, n),       # geo_distance_km
            rng.uniform(0, 86_400, n),       # time_since_last_ok (seconds)
        ]).astype(float)

        # Synthetic labels – heuristic logic to mimic real patterns
        y_raw = np.zeros(n, dtype=int)  # low
        medium_mask = (
            (X[:, 0] >= 3) |  # ≥3 failed attempts
            (X[:, 3] == 1) |  # new device
            (X[:, 4] == 1)    # vpn/proxy
        )
        high_mask = (
            (X[:, 0] >= 8) |  # ≥8 failed attempts
            (X[:, 4] == 1) & (X[:, 3] == 1) |  # vpn + new device
            (X[:, 5] > 10_000)  # large geo jump
        )
        y_raw[medium_mask] = 1
        y_raw[high_mask] = 2

        labels = np.array(RISK_LABELS)
        self._label_encoder.fit(labels)
        assert self._pipeline is not None
        self._pipeline.fit(X, y_raw)
        self._is_fitted = True

    def _extract_features(self, inputs: Dict[str, Any]) -> np.ndarray:
        return np.array([[
            float(inputs.get("failed_attempts", 0)),
            float(inputs.get("ip_entropy", _ip_to_entropy(inputs.get("ip", "0.0.0.0")))),
            float(inputs.get("hour_of_day", time.localtime().tm_hour)),
            float(bool(inputs.get("new_device", False))),
            float(bool(inputs.get("vpn_proxy", False))),
            float(inputs.get("geo_distance_km", 0.0)),
            float(inputs.get("time_since_last_ok", 86_400.0)),
        ]])

    async def predict(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        if not self._is_fitted or self._pipeline is None:
            return {"risk_label": "medium", "risk_score": 0.5, "probabilities": {}}

        X = self._extract_features(inputs)
        pred_idx = int(self._pipeline.predict(X)[0])
        proba = self._pipeline.predict_proba(X)[0].tolist()

        risk_label = RISK_LABELS[pred_idx]
        risk_score = round(proba[pred_idx], 4)
        probabilities = {label: round(p, 4) for label, p in zip(RISK_LABELS, proba)}

        return {
            "risk_label": risk_label,
            "risk_score": risk_score,
            "probabilities": probabilities,
        }

    async def metrics(self) -> Dict[str, float]:
        return {
            "fitted": float(self._is_fitted),
            "n_estimators": float(
                self._pipeline.named_steps["clf"].n_estimators
                if self._pipeline else 0
            ),
        }


# ─────────────────────────────────────────────────────────────────────────────
# 2. AnomalyDetector
# ─────────────────────────────────────────────────────────────────────────────

@model(
    name="auth_anomaly_detector",
    version="v1",
    device="cpu",
    batch_size=32,
    timeout_ms=5000.0,
    tags=["auth", "security", "anomaly", "sklearn"],
)
class AnomalyDetector(AquiliaModel):
    """
    Detects anomalous session / auth patterns using ``IsolationForest``.

    Input features
    --------------
    ``requests_per_minute`` – float, API call rate in the current session
    ``unique_endpoints``    – int,   number of distinct endpoints hit
    ``session_age_seconds`` – float, how long the session has been active
    ``error_rate``          – float, fraction of 4xx/5xx responses (0..1)
    ``payload_size_mean``   – float, mean request body size in bytes
    ``ip_entropy``          – float, IP address surprise score 0..1

    Output
    ------
    ``is_anomaly``  – bool
    ``anomaly_score``– float, negative = more anomalous (IsolationForest convention)
    ``verdict``     – str, "normal" or "anomaly"
    """

    FEATURE_NAMES = [
        "requests_per_minute",
        "unique_endpoints",
        "session_age_seconds",
        "error_rate",
        "payload_size_mean",
        "ip_entropy",
    ]

    # Contamination: expected fraction of anomalies in production traffic
    CONTAMINATION = 0.05

    def __init__(self) -> None:
        self._pipeline: Optional[Pipeline] = None
        self._threshold: float = 0.0
        self._is_fitted = False

    async def load(self, artifacts_dir: str, device: str) -> None:
        self._pipeline = Pipeline([
            ("scaler", StandardScaler()),
            ("iforest", IsolationForest(
                n_estimators=200,
                contamination=self.CONTAMINATION,
                max_samples="auto",
                random_state=42,
                n_jobs=-1,
            )),
        ])
        self._warm_start()
        logger.info("AnomalyDetector loaded and warm-started.")

    def _warm_start(self) -> None:
        rng = np.random.default_rng(0)
        n_normal, n_anomaly = 5_000, 250

        # Normal traffic
        X_normal = np.column_stack([
            rng.uniform(1, 60, n_normal),       # requests_per_minute
            rng.integers(1, 12, n_normal),       # unique_endpoints
            rng.uniform(60, 3_600, n_normal),    # session_age_seconds
            rng.uniform(0, 0.05, n_normal),      # error_rate (low)
            rng.uniform(50, 2_000, n_normal),    # payload_size_mean
            rng.uniform(0, 0.3, n_normal),       # ip_entropy (trusted IPs)
        ])

        # Anomalous traffic (high rate, many errors, large payloads)
        X_anomaly = np.column_stack([
            rng.uniform(200, 2_000, n_anomaly),  # very high request rate
            rng.integers(20, 50, n_anomaly),     # many endpoints
            rng.uniform(0, 30, n_anomaly),       # very short session
            rng.uniform(0.3, 1.0, n_anomaly),   # high error rate
            rng.uniform(5_000, 50_000, n_anomaly),# large payloads
            rng.uniform(0.7, 1.0, n_anomaly),   # high IP entropy
        ])

        X = np.vstack([X_normal, X_anomaly]).astype(float)
        assert self._pipeline is not None
        self._pipeline.fit(X)
        self._is_fitted = True

    def _extract_features(self, inputs: Dict[str, Any]) -> np.ndarray:
        return np.array([[
            float(inputs.get("requests_per_minute", 10.0)),
            float(inputs.get("unique_endpoints", 3)),
            float(inputs.get("session_age_seconds", 300.0)),
            float(inputs.get("error_rate", 0.0)),
            float(inputs.get("payload_size_mean", 256.0)),
            float(inputs.get("ip_entropy", 0.1)),
        ]])

    async def predict(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        if not self._is_fitted or self._pipeline is None:
            return {"is_anomaly": False, "anomaly_score": 0.0, "verdict": "normal"}

        X = self._extract_features(inputs)
        # IsolationForest returns -1 (anomaly) or 1 (normal)
        pred = int(self._pipeline.predict(X)[0])
        raw_score = float(self._pipeline.named_steps["iforest"].score_samples(
            self._pipeline.named_steps["scaler"].transform(X)
        )[0])

        is_anomaly = pred == -1
        return {
            "is_anomaly": is_anomaly,
            "anomaly_score": round(raw_score, 6),
            "verdict": "anomaly" if is_anomaly else "normal",
        }

    async def metrics(self) -> Dict[str, float]:
        return {
            "fitted": float(self._is_fitted),
            "contamination": self.CONTAMINATION,
        }


# ─────────────────────────────────────────────────────────────────────────────
# 3. BruteForceDetector  (online / incremental learning)
# ─────────────────────────────────────────────────────────────────────────────

@model(
    name="brute_force_detector",
    version="v1",
    device="cpu",
    batch_size=128,
    timeout_ms=2000.0,
    tags=["auth", "security", "online-learning", "sklearn"],
)
class BruteForceDetector(AquiliaModel):
    """
    Lightweight *online-learning* brute-force detector.

    Uses ``SGDClassifier`` (partial_fit) so the model can be updated
    continuously as new labelled events arrive – no full retraining needed.

    Input features
    --------------
    ``attempts_last_1m``   – int,   failed logins in the last 1 minute
    ``attempts_last_5m``   – int,   failed logins in the last 5 minutes
    ``attempts_last_15m``  – int,   failed logins in the last 15 minutes
    ``distinct_usernames`` – int,   unique usernames tried from this IP
    ``distinct_ips``       – int,   IPs used by this username
    ``inter_attempt_secs`` – float, avg seconds between consecutive attempts
    ``is_known_bad_ip``    – bool,  IP on a threat-intel blocklist

    Output
    ------
    ``is_brute_force``  – bool
    ``confidence``      – float, model probability 0..1
    ``verdict``         – str, "clean" or "brute_force"
    """

    FEATURE_NAMES = [
        "attempts_last_1m",
        "attempts_last_5m",
        "attempts_last_15m",
        "distinct_usernames",
        "distinct_ips",
        "inter_attempt_secs",
        "is_known_bad_ip",
    ]
    CLASSES = np.array([0, 1])  # 0=clean, 1=brute_force

    def __init__(self) -> None:
        self._scaler = StandardScaler()
        # NOTE: class_weight="balanced" is incompatible with partial_fit;
        # we pass explicit sample_weight during warm-start instead.
        self._clf = SGDClassifier(
            loss="log_loss",        # probabilistic output
            penalty="l2",
            alpha=1e-4,
            max_iter=1000,
            tol=1e-3,
            random_state=42,
        )
        self._is_fitted = False
        self._n_partial_fits: int = 0

    async def load(self, artifacts_dir: str, device: str) -> None:
        self._warm_start()
        logger.info("BruteForceDetector loaded and warm-started.")

    def _warm_start(self) -> None:
        rng = np.random.default_rng(7)
        n = 4_000

        X_clean = np.column_stack([
            rng.integers(0, 2, n // 2),        # attempts_last_1m
            rng.integers(0, 5, n // 2),        # attempts_last_5m
            rng.integers(0, 10, n // 2),       # attempts_last_15m
            np.ones(n // 2),                   # distinct_usernames
            np.ones(n // 2),                   # distinct_ips
            rng.uniform(60, 3_600, n // 2),   # inter_attempt_secs (slow)
            np.zeros(n // 2),                  # is_known_bad_ip
        ])
        X_attack = np.column_stack([
            rng.integers(5, 30, n // 2),       # high rate
            rng.integers(20, 120, n // 2),
            rng.integers(50, 300, n // 2),
            rng.integers(1, 50, n // 2),       # credential stuffing: many usernames
            rng.integers(1, 20, n // 2),
            rng.uniform(0.1, 5.0, n // 2),    # very fast attempts
            rng.integers(0, 2, n // 2),
        ])

        X_all = np.vstack([X_clean, X_attack]).astype(float)
        y_all = np.array([0] * (n // 2) + [1] * (n // 2))

        # Balance classes via sample_weight (partial_fit doesn't accept class_weight="balanced")
        class_counts = np.bincount(y_all)
        sample_weight = np.where(y_all == 0,
                                 1.0 / class_counts[0],
                                 1.0 / class_counts[1])

        # Fit the scaler on all data then do initial partial_fit
        X_scaled = self._scaler.fit_transform(X_all)
        self._clf.partial_fit(X_scaled, y_all, classes=self.CLASSES,
                              sample_weight=sample_weight)
        self._is_fitted = True
        self._n_partial_fits += 1

    def _extract_features(self, inputs: Dict[str, Any]) -> np.ndarray:
        return np.array([[
            float(inputs.get("attempts_last_1m", 0)),
            float(inputs.get("attempts_last_5m", 0)),
            float(inputs.get("attempts_last_15m", 0)),
            float(inputs.get("distinct_usernames", 1)),
            float(inputs.get("distinct_ips", 1)),
            float(inputs.get("inter_attempt_secs", 300.0)),
            float(bool(inputs.get("is_known_bad_ip", False))),
        ]])

    async def predict(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        if not self._is_fitted:
            return {"is_brute_force": False, "confidence": 0.0, "verdict": "clean"}

        X = self._extract_features(inputs)
        X_scaled = self._scaler.transform(X)
        pred = int(self._clf.predict(X_scaled)[0])
        proba = self._clf.predict_proba(X_scaled)[0]

        is_brute_force = pred == 1
        confidence = round(float(proba[1]), 4)

        return {
            "is_brute_force": is_brute_force,
            "confidence": confidence,
            "verdict": "brute_force" if is_brute_force else "clean",
        }

    async def partial_fit(self, X_raw: np.ndarray, y: np.ndarray) -> None:
        """Incremental update -- call with new labelled events."""
        X_scaled = self._scaler.transform(X_raw)
        self._clf.partial_fit(X_scaled, y, classes=self.CLASSES)
        self._n_partial_fits += 1
        logger.debug("BruteForceDetector partial_fit #%d", self._n_partial_fits)

    async def metrics(self) -> Dict[str, float]:
        return {
            "fitted": float(self._is_fitted),
            "partial_fits": float(self._n_partial_fits),
        }


# ─────────────────────────────────────────────────────────────────────────────
# 4. UserBehaviorClassifier
# ─────────────────────────────────────────────────────────────────────────────

@model(
    name="user_behavior_classifier",
    version="v1",
    device="cpu",
    batch_size=32,
    timeout_ms=8000.0,
    tags=["auth", "security", "behaviour", "sklearn"],
)
class UserBehaviorClassifier(AquiliaModel):
    """
    Classifies long-term user behaviour to support adaptive authentication.

    Labels: ``normal``, ``suspicious``, ``bot``, ``compromised``

    Mixed-type features (numeric + categorical) processed via
    ``ColumnTransformer`` → ``GradientBoostingClassifier``.

    Input features
    --------------
    ``avg_session_duration``  – float, seconds
    ``avg_requests_per_sess`` – float, API calls per session
    ``login_hour_mode``       – str,   dominant login hour bucket
                                       ("business" / "evening" / "night")
    ``device_change_rate``    – float, fraction of sessions from a new device
    ``mfa_pass_rate``         – float, MFA success rate (0..1)
    ``days_since_pw_change``  – float
    ``failed_login_rate``     – float, fraction of login attempts that fail

    Output
    ------
    ``behavior_label``   – str, one of BEHAVIOR_LABELS
    ``behavior_score``   – float, probability of predicted class
    ``probabilities``    – dict, label → probability
    """

    NUMERIC_FEATURES = [0, 1, 3, 4, 5, 6]  # column indices in feature array
    CATEGORICAL_FEATURES = [2]              # login_hour_mode column

    def __init__(self) -> None:
        self._pipeline: Optional[Pipeline] = None
        self._label_encoder = LabelEncoder()
        self._is_fitted = False

    async def load(self, artifacts_dir: str, device: str) -> None:
        numeric_transformer = Pipeline([
            ("scaler", StandardScaler()),
        ])
        categorical_transformer = Pipeline([
            ("ohe", OneHotEncoder(
                categories=[["business", "evening", "night"]],
                handle_unknown="ignore",
            )),
        ])

        preprocessor = ColumnTransformer(
            transformers=[
                ("num", numeric_transformer, self.NUMERIC_FEATURES),
                ("cat", categorical_transformer, self.CATEGORICAL_FEATURES),
            ]
        )

        self._pipeline = Pipeline([
            ("preprocessor", preprocessor),
            ("clf", GradientBoostingClassifier(
                n_estimators=100,
                max_depth=4,
                learning_rate=0.1,
                subsample=0.8,
                random_state=42,
            )),
        ])
        self._label_encoder.fit(BEHAVIOR_LABELS)
        self._warm_start()
        logger.info("UserBehaviorClassifier loaded and warm-started.")

    def _warm_start(self) -> None:
        rng = np.random.default_rng(13)
        n_per_class = 800
        n = n_per_class * 4

        hour_buckets = np.array(["business", "evening", "night"])

        # ── normal ──────────────────────────────────────────────────
        X_normal = np.column_stack([
            rng.uniform(300, 1_800, n_per_class),    # avg_session_duration
            rng.uniform(5, 50, n_per_class),          # avg_requests_per_sess
            rng.choice(["business", "evening"], n_per_class),  # hour_mode
            rng.uniform(0, 0.1, n_per_class),         # device_change_rate
            rng.uniform(0.9, 1.0, n_per_class),       # mfa_pass_rate
            rng.uniform(0, 90, n_per_class),           # days_since_pw_change
            rng.uniform(0, 0.05, n_per_class),         # failed_login_rate
        ])

        # ── suspicious ──────────────────────────────────────────────
        X_suspicious = np.column_stack([
            rng.uniform(10, 120, n_per_class),
            rng.uniform(100, 500, n_per_class),       # high request count
            rng.choice(["night"], n_per_class),        # always night
            rng.uniform(0.3, 0.8, n_per_class),       # frequent device change
            rng.uniform(0.5, 0.9, n_per_class),
            rng.uniform(180, 365, n_per_class),        # old password
            rng.uniform(0.1, 0.4, n_per_class),
        ])

        # ── bot ──────────────────────────────────────────────────────
        X_bot = np.column_stack([
            rng.uniform(1, 10, n_per_class),           # very short sessions
            rng.uniform(500, 2_000, n_per_class),      # many requests
            rng.choice(hour_buckets, n_per_class),
            np.ones(n_per_class) * 0.0,                # never changes device
            np.ones(n_per_class),                       # always passes MFA
            rng.uniform(0, 10, n_per_class),
            np.zeros(n_per_class),                      # never fails login
        ])

        # ── compromised ──────────────────────────────────────────────
        X_compromised = np.column_stack([
            rng.uniform(30, 600, n_per_class),
            rng.uniform(20, 200, n_per_class),
            rng.choice(["night"], n_per_class),
            np.ones(n_per_class),                      # always new device
            rng.uniform(0.0, 0.5, n_per_class),        # low MFA pass rate
            rng.uniform(0, 5, n_per_class),             # very recent pw change
            rng.uniform(0.3, 0.8, n_per_class),
        ])

        X_all = np.vstack([X_normal, X_suspicious, X_bot, X_compromised])
        y_all = np.array(
            [0] * n_per_class +   # normal
            [1] * n_per_class +   # suspicious
            [2] * n_per_class +   # bot
            [3] * n_per_class     # compromised
        )

        assert self._pipeline is not None
        self._pipeline.fit(X_all, y_all)
        self._is_fitted = True

    def _extract_features(self, inputs: Dict[str, Any]) -> np.ndarray:
        hour = int(inputs.get("login_hour_mode_raw", time.localtime().tm_hour))
        hour_bucket = _hour_bucket(hour) if isinstance(
            inputs.get("login_hour_mode"), (int, float)
        ) else str(inputs.get("login_hour_mode", "business"))

        return np.array([[
            float(inputs.get("avg_session_duration", 600.0)),
            float(inputs.get("avg_requests_per_sess", 20.0)),
            hour_bucket,
            float(inputs.get("device_change_rate", 0.0)),
            float(inputs.get("mfa_pass_rate", 1.0)),
            float(inputs.get("days_since_pw_change", 30.0)),
            float(inputs.get("failed_login_rate", 0.0)),
        ]], dtype=object)

    async def predict(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        if not self._is_fitted or self._pipeline is None:
            return {
                "behavior_label": "normal",
                "behavior_score": 0.5,
                "probabilities": {},
            }

        X = self._extract_features(inputs)
        pred_idx = int(self._pipeline.predict(X)[0])
        proba = self._pipeline.predict_proba(X)[0].tolist()

        behavior_label = BEHAVIOR_LABELS[pred_idx]
        behavior_score = round(proba[pred_idx], 4)
        probabilities = {
            label: round(p, 4)
            for label, p in zip(BEHAVIOR_LABELS, proba)
        }

        return {
            "behavior_label": behavior_label,
            "behavior_score": behavior_score,
            "probabilities": probabilities,
        }

    async def metrics(self) -> Dict[str, float]:
        return {"fitted": float(self._is_fitted)}
