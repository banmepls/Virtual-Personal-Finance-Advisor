"""
app/ml/isolation_forest.py
--------------------------
Isolation Forest wrapper for anomaly detection.

Isolation Forest works by randomly partitioning data;
anomalies require fewer splits to isolate (lower average path length).
Score normalized to [0, 1], where 1 = highly anomalous.
"""
import numpy as np
from sklearn.ensemble import IsolationForest as _IsolationForest
import logging

logger = logging.getLogger(__name__)


class IsolationForestModel:
    def __init__(self, contamination: float = 0.1, n_estimators: int = 100, random_state: int = 42):
        self._model = _IsolationForest(
            contamination=contamination,
            n_estimators=n_estimators,
            random_state=random_state,
        )
        self._is_trained = False

    def train(self, X: np.ndarray):
        """Fit the model on historical 'normal' data."""
        self._model.fit(X)
        self._is_trained = True
        logger.info(f"[IsolationForest] Trained on {X.shape[0]} samples, {X.shape[1]} features")

    def score(self, x: np.ndarray) -> float:
        """
        Returns anomaly score in [0, 1].
        IsolationForest returns negative scores (more negative = more anomalous),
        so we invert and normalize.
        """
        if not self._is_trained:
            # Auto-train on the single point if no history — lowest confidence
            self.train(x.reshape(1, -1) if x.ndim == 1 else x)

        raw = self._model.score_samples(x.reshape(1, -1) if x.ndim == 1 else x)
        # sklearn scores are in (-inf, 0], most anomalous ≈ -0.5 or lower
        # Normalize: typical range [-0.6, 0.0] → [0.0, 1.0]
        normalized = float(np.clip(-raw[0] * 2.0, 0.0, 1.0))
        return normalized

    def predict(self, x: np.ndarray) -> int:
        """Returns -1 for anomaly, 1 for normal (sklearn convention)."""
        if not self._is_trained:
            return 1
        return int(self._model.predict(x.reshape(1, -1) if x.ndim == 1 else x)[0])
