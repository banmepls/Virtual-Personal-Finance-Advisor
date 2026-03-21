"""
app/ml/autoencoder.py
---------------------
Lightweight numpy-based autoencoder for anomaly detection.

The core idea: train a compact encoder-decoder on "normal" portfolio snapshots.
At inference, compute MSE (reconstruction error).
High MSE → the pattern deviates strongly from learned normal behavior.

This implementation uses a simple two-layer linear autoencoder (no PyTorch/TF dependency)
implemented via numpy SVD-based dimensionality reduction, suitable for tabular financial data.
"""
import numpy as np
import logging

logger = logging.getLogger(__name__)


class AutoencoderModel:
    """
    PCA-based Autoencoder approximation using SVD truncation.
    Lightweight replacement for a true LSTM Autoencoder — same principle:
    learn the manifold of normal data, measure reconstruction error at inference.
    """

    def __init__(self, n_components: int = 2):
        self.n_components = n_components
        self._components: np.ndarray | None = None  # V^T from SVD
        self._mean: np.ndarray | None = None
        self._max_mse: float = 1.0  # for normalization
        self._is_trained = False

    def train(self, X: np.ndarray):
        """
        Fit on normal data matrix X of shape (n_samples, n_features).
        Stores principal components for reconstruction.
        """
        self._mean = X.mean(axis=0)
        X_centered = X - self._mean

        n_comp = min(self.n_components, X_centered.shape[0], X_centered.shape[1])
        U, S, Vt = np.linalg.svd(X_centered, full_matrices=False)
        self._components = Vt[:n_comp]  # shape: (n_components, n_features)

        # Compute train reconstruction error to calibrate normalization
        train_errors = [self._reconstruction_mse(X[i]) for i in range(len(X))]
        self._max_mse = max(train_errors) if train_errors else 1.0
        self._is_trained = True
        logger.info(f"[Autoencoder] Trained on {X.shape[0]} samples, max_mse={self._max_mse:.4f}")

    def _reconstruction_mse(self, x: np.ndarray) -> float:
        x_c = x - self._mean
        # Project into reduced space then reconstruct
        encoded = self._components @ x_c        # shape: (n_components,)
        decoded = self._components.T @ encoded  # shape: (n_features,)
        reconstructed = decoded + self._mean
        return float(np.mean((x - reconstructed) ** 2))

    def score(self, x: np.ndarray) -> float:
        """
        Returns anomaly score in [0, 1].
        High score = high reconstruction error = likely anomaly.
        """
        if not self._is_trained:
            # No training data: use a flat snapshot to auto-train
            X_tmp = np.stack([x, x * 0.95, x * 1.05])
            self.train(X_tmp)

        mse = self._reconstruction_mse(x)
        normalized = float(np.clip(mse / (self._max_mse + 1e-8), 0.0, 1.0))
        return normalized
