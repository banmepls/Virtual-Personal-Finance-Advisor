"""
app/ml/one_class_svm.py
-----------------------
One-Class SVM wrapper for anomaly detection.

Learns a hypersphere around normal data in a kernel-mapped feature space.
Points outside the sphere are flagged as anomalies.
Score normalized to [0, 1], where 1 = highly anomalous.
"""
import numpy as np
from sklearn.svm import OneClassSVM as _OneClassSVM
from sklearn.preprocessing import StandardScaler
import logging

logger = logging.getLogger(__name__)


class OneClassSVMModel:
    def __init__(self, nu: float = 0.1, kernel: str = "rbf", gamma: str = "scale"):
        """
        nu: upper bound on fraction of training errors (≈ expected anomaly rate)
        kernel: RBF is the most common for financial time-series
        """
        self._model = _OneClassSVM(nu=nu, kernel=kernel, gamma=gamma)
        self._scaler = StandardScaler()
        self._is_trained = False
        self._min_score: float = -1.0
        self._max_score: float = 1.0

    def train(self, X: np.ndarray):
        """Fit the model on normal historical data."""
        X_scaled = self._scaler.fit_transform(X)
        self._model.fit(X_scaled)
        # Calibrate score range
        raw_scores = self._model.score_samples(X_scaled)
        self._min_score = float(raw_scores.min())
        self._max_score = float(raw_scores.max())
        self._is_trained = True
        logger.info(f"[OneClassSVM] Trained on {X.shape[0]} samples. Score range: [{self._min_score:.3f}, {self._max_score:.3f}]")

    def score(self, x: np.ndarray) -> float:
        """
        Returns anomaly score in [0, 1].
        High score = outside the learned normal hypersphere.
        """
        if not self._is_trained:
            X_tmp = np.stack([x, x * 0.95, x * 1.05, x * 0.90, x * 1.10])
            self.train(X_tmp)

        x_scaled = self._scaler.transform(x.reshape(1, -1))
        raw = float(self._model.score_samples(x_scaled)[0])

        # raw: negative scores = anomaly, positive = normal
        # Normalize: [min_score, max_score] → [1, 0] (inverted)
        score_range = self._max_score - self._min_score
        if score_range < 1e-10:
            return 0.5
        normalized = 1.0 - (raw - self._min_score) / score_range
        return float(np.clip(normalized, 0.0, 1.0))

    def predict(self, x: np.ndarray) -> int:
        if not self._is_trained:
            return 1
        x_scaled = self._scaler.transform(x.reshape(1, -1))
        return int(self._model.predict(x_scaled)[0])
