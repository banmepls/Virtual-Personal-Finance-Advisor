"""
app/ml/voting_ensemble.py
--------------------------
Calibrated Soft Majority Voting ensemble.

Formula:
    S_weighted = (w_if * S_if + w_ae * S_ae + w_svm * S_svm) / (w_if + w_ae + w_svm)
    is_anomaly = S_weighted > threshold

Model weights reflect relative reliability on financial tabular data:
  - LSTM Autoencoder: highest sensitivity to temporal patterns → 0.40
  - Isolation Forest: excellent at detecting outliers in large datasets → 0.35
  - One-Class SVM:    strong structural boundary detection → 0.25
"""
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

DEFAULT_WEIGHTS = (0.35, 0.40, 0.25)   # (isolation_forest, autoencoder, svm)
DEFAULT_THRESHOLD = 0.5


@dataclass
class VotingResult:
    isolation_score: float
    autoencoder_mse: float
    svm_score: float
    weighted_avg_score: float
    is_anomaly: bool
    confidence: str   # "LOW" | "MEDIUM" | "HIGH"
    notes: str


class VotingEnsemble:
    def __init__(
        self,
        weights: tuple[float, float, float] = DEFAULT_WEIGHTS,
        threshold: float = DEFAULT_THRESHOLD,
    ):
        self.w_if, self.w_ae, self.w_svm = weights
        self.threshold = threshold

    def vote(
        self,
        isolation_score: float,
        autoencoder_score: float,
        svm_score: float,
    ) -> VotingResult:
        """
        Compute weighted ensemble score and determine anomaly decision.

        Args:
            isolation_score:   IsolationForest score [0,1]
            autoencoder_score: Autoencoder MSE score  [0,1]
            svm_score:         OneClassSVM score      [0,1]

        Returns:
            VotingResult with full breakdown and decision
        """
        total_weight = self.w_if + self.w_ae + self.w_svm
        weighted = (
            self.w_if * isolation_score +
            self.w_ae * autoencoder_score +
            self.w_svm * svm_score
        ) / total_weight

        is_anomaly = weighted > self.threshold

        # Votes from individual models (majority count for confidence)
        individual_votes = [
            isolation_score > self.threshold,
            autoencoder_score > self.threshold,
            svm_score > self.threshold,
        ]
        agreed = sum(individual_votes)

        if agreed == 3:
            confidence = "HIGH"
        elif agreed == 2:
            confidence = "MEDIUM"
        else:
            confidence = "LOW"

        notes = (
            f"Weighted score: {weighted:.3f} | "
            f"IF={isolation_score:.3f} AE={autoencoder_score:.3f} SVM={svm_score:.3f} | "
            f"Models agreed: {agreed}/3 | Confidence: {confidence}"
        )
        logger.info(f"[VotingEnsemble] {notes} → is_anomaly={is_anomaly}")

        return VotingResult(
            isolation_score=isolation_score,
            autoencoder_mse=autoencoder_score,
            svm_score=svm_score,
            weighted_avg_score=weighted,
            is_anomaly=is_anomaly,
            confidence=confidence,
            notes=notes,
        )
