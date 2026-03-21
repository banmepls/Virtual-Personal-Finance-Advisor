"""
app/ml/anomaly_service.py
--------------------------
Orchestrator that:
1. Converts portfolio snapshot → numpy feature vector
2. Trains models on-the-fly if not trained (uses synthetic normal history)
3. Runs all 3 models and applies voting ensemble
4. Returns VotingResult (can be saved to AnomalyLog by the endpoint)
"""
import numpy as np
import logging
from app.ml.isolation_forest import IsolationForestModel
from app.ml.autoencoder import AutoencoderModel
from app.ml.one_class_svm import OneClassSVMModel
from app.ml.voting_ensemble import VotingEnsemble, VotingResult

logger = logging.getLogger(__name__)


def _portfolio_to_features(positions: list[dict]) -> np.ndarray:
    """
    Convert a list of portfolio positions to a 1D numpy feature vector.
    Features per position: [quantity, avg_buy_price, current_value, unrealized_pnl]
    Result: flattened fixed-size vector (padded to max 10 positions).
    """
    MAX_POSITIONS = 10
    features_per_pos = 4  # quantity, avgBuyPrice, currentValue, unrealizedPnL

    vec = np.zeros(MAX_POSITIONS * features_per_pos, dtype=np.float32)
    for i, pos in enumerate(positions[:MAX_POSITIONS]):
        offset = i * features_per_pos
        vec[offset]     = float(pos.get("quantity", 0))
        vec[offset + 1] = float(pos.get("avgBuyPrice", pos.get("avg_buy_price", 0)))
        vec[offset + 2] = float(pos.get("currentValue", pos.get("current_value", 0)))
        vec[offset + 3] = float(pos.get("unrealizedPnL", pos.get("unrealized_pnl", 0)))
    return vec


def _generate_normal_history(reference: np.ndarray, n_samples: int = 50) -> np.ndarray:
    """
    Generate synthetic 'normal' training data around a reference vector.
    Adds ±5% noise to simulate normal portfolio variation.
    Used when no real historical data is available yet.
    """
    rng = np.random.default_rng(42)
    noise = rng.uniform(-0.05, 0.05, size=(n_samples, len(reference)))
    history = reference[np.newaxis, :] * (1 + noise)
    return history.astype(np.float32)


# ── Module-level singleton models (persist across requests) ───────────────────
_if_model = IsolationForestModel(contamination=0.1)
_ae_model = AutoencoderModel(n_components=3)
_svm_model = OneClassSVMModel(nu=0.1)
_ensemble = VotingEnsemble()
_models_trained = False


def analyze_portfolio(positions: list[dict]) -> VotingResult:
    """
    Main entry point.
    Takes raw portfolio positions list, returns VotingResult.
    Thread-safe for asyncio (pure numpy, no I/O).
    """
    global _models_trained

    features = _portfolio_to_features(positions)

    # Auto-train on synthetic normal data if no real history is loaded yet
    if not _models_trained:
        X_train = _generate_normal_history(features)
        _if_model.train(X_train)
        _ae_model.train(X_train)
        _svm_model.train(X_train)
        _models_trained = True
        logger.info("[AnomalyService] Models auto-trained on synthetic normal history")

    if_score  = _if_model.score(features)
    ae_score  = _ae_model.score(features)
    svm_score = _svm_model.score(features)

    result = _ensemble.vote(if_score, ae_score, svm_score)
    return result


def retrain(historical_snapshots: list[list[dict]]):
    """
    Retrain all models on real historical portfolio data.
    Call this when enough historical data has been accumulated.
    """
    global _models_trained
    X = np.array([_portfolio_to_features(snap) for snap in historical_snapshots])
    _if_model.train(X)
    _ae_model.train(X)
    _svm_model.train(X)
    _models_trained = True
    logger.info(f"[AnomalyService] Models retrained on {len(X)} historical snapshots")
