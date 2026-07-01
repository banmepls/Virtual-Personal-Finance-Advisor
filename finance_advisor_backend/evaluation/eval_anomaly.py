"""
evaluation/eval_anomaly.py
==========================
Quantitative evaluation of the 3-model anomaly-detection ensemble.

The script fabricates a *labeled* data set (which the production system never
has, because portfolio anomalies are unlabeled in the wild):

  * Class 0 (normal)  : the reference portfolio perturbed by +/-5% noise,
                        exactly the distribution the models train on
                        (`_generate_normal_history`).
  * Class 1 (anomaly) : four families of large, controlled injections
                        (value spike x5-x10, 80% crash, 90% concentration,
                        aberrant quantity).

Protocol (standard supervised evaluation of unsupervised detectors):

  train  = 400 normal portfolios              -> fit the "normal" manifold
  val    = 300 normal + 300 anomalies         -> select each model's decision
                                                 threshold by maximising F1
  test   = 500 normal + 500 anomalies         -> report P / R / F1 / ROC-AUC

The *real* model classes are used (IsolationForestModel, AutoencoderModel,
OneClassSVMModel) together with the production calibrated soft-voting ensemble
(weights 0.35 / 0.40 / 0.25).  ROC-AUC is threshold-independent and is the
headline evidence for the ensemble's superior discrimination.

Outputs
-------
  * evaluation/results_anomaly.json         — all raw numbers for the thesis
  * evaluation/figures/roc.{pdf,png}
  * evaluation/figures/score_dist.{pdf,png}
  * evaluation/figures/f1_threshold.{pdf,png}

Run from the backend root:
    python -m evaluation.eval_anomaly
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.metrics import roc_auc_score, roc_curve

from app.ml.anomaly_service import _portfolio_to_features
from app.ml.isolation_forest import IsolationForestModel
from app.ml.autoencoder import AutoencoderModel
from app.ml.one_class_svm import OneClassSVMModel
from app.ml.voting_ensemble import VotingEnsemble, DEFAULT_WEIGHTS, DEFAULT_THRESHOLD

SEED = 42
N_TRAIN = 400
N_VAL_NORMAL, N_VAL_ANOM = 300, 300
N_TEST_NORMAL, N_TEST_ANOM = 500, 500
NOISE = 0.05

FIG_DIR = Path(__file__).resolve().parent / "figures"
FIG_DIR.mkdir(exist_ok=True)
OUT_JSON = Path(__file__).resolve().parent / "results_anomaly.json"

BASE = [
    {"quantity": 5.0,  "avgBuyPrice": 155.20, "currentValue": 937.50,  "unrealizedPnL": 162.50},
    {"quantity": 0.05, "avgBuyPrice": 35000.0, "currentValue": 3390.00, "unrealizedPnL": 1390.00},
    {"quantity": 3.0,  "avgBuyPrice": 420.00, "currentValue": 2625.00, "unrealizedPnL": 1365.00},
    {"quantity": 4.0,  "avgBuyPrice": 280.00, "currentValue": 780.00,  "unrealizedPnL": -340.00},
    {"quantity": 2.0,  "avgBuyPrice": 380.00, "currentValue": 831.00,  "unrealizedPnL": 71.00},
    {"quantity": 10.0, "avgBuyPrice": 440.00, "currentValue": 4550.00, "unrealizedPnL": 150.00},
]
FIELDS = ("quantity", "avgBuyPrice", "currentValue", "unrealizedPnL")
ANOMALY_TYPES = ("value_spike", "asset_crash", "concentration", "aberrant_qty")
MODEL_NAMES = ["Isolation Forest", "PCA Autoencoder", "One-Class SVM", "Ansamblu (vot ponderat)"]


def _perturb_normal(r: np.random.Generator) -> list[dict]:
    return [{f: float(pos[f]) * (1.0 + r.uniform(-NOISE, NOISE)) for f in FIELDS} for pos in BASE]


def _inject(kind: str, r: np.random.Generator) -> list[dict]:
    pf = _perturb_normal(r)
    idx = int(r.integers(0, len(pf)))
    p = pf[idx]
    if kind == "value_spike":
        f = float(r.uniform(5.0, 10.0))
        p["currentValue"] *= f
        p["unrealizedPnL"] *= f
    elif kind == "asset_crash":
        cost = p["avgBuyPrice"] * p["quantity"]
        p["currentValue"] = 0.2 * cost
        p["unrealizedPnL"] = -0.8 * cost
    elif kind == "concentration":
        others = sum(q["currentValue"] for j, q in enumerate(pf) if j != idx)
        p["currentValue"] = 9.0 * others
        p["unrealizedPnL"] = 0.3 * p["currentValue"]
    elif kind == "aberrant_qty":
        p["quantity"] *= float(r.uniform(20.0, 50.0))
    return pf


def _make_split(n_normal: int, n_anom: int, r: np.random.Generator):
    X = [_portfolio_to_features(_perturb_normal(r)) for _ in range(n_normal)]
    types = ["normal"] * n_normal
    per = n_anom // len(ANOMALY_TYPES)
    for kind in ANOMALY_TYPES:
        for _ in range(per):
            X.append(_portfolio_to_features(_inject(kind, r)))
            types.append(kind)
    y = np.array([0] * n_normal + [1] * (per * len(ANOMALY_TYPES)))
    return np.stack(X), y, types


def build_dataset():
    r_tr = np.random.default_rng(SEED)
    r_va = np.random.default_rng(SEED + 1)
    r_te = np.random.default_rng(SEED + 2)
    X_train = np.stack([_portfolio_to_features(_perturb_normal(r_tr)) for _ in range(N_TRAIN)])
    X_val, y_val, _ = _make_split(N_VAL_NORMAL, N_VAL_ANOM, r_va)
    X_test, y_test, types_test = _make_split(N_TEST_NORMAL, N_TEST_ANOM, r_te)
    return X_train, X_val, y_val, X_test, y_test, types_test


def confusion(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    tp = int(np.sum((y_pred == 1) & (y_true == 1)))
    fp = int(np.sum((y_pred == 1) & (y_true == 0)))
    tn = int(np.sum((y_pred == 0) & (y_true == 0)))
    fn = int(np.sum((y_pred == 0) & (y_true == 1)))
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return {"TP": tp, "FP": fp, "TN": tn, "FN": fn,
            "precision": precision, "recall": recall, "f1": f1}


def calibrate_threshold(scores_val: np.ndarray, y_val: np.ndarray):
    """Return (threshold, val_f1) that maximises F1 on the validation split."""
    grid = np.round(np.arange(0.02, 0.99, 0.01), 2)
    f1s = [confusion(y_val, (scores_val > t).astype(int))["f1"] for t in grid]
    i = int(np.argmax(f1s))
    return float(grid[i]), float(f1s[i])


def main():
    X_train, X_val, y_val, X_test, y_test, types_test = build_dataset()
    print(f"[data] train={len(X_train)} normal | val={len(y_val)} | test={len(y_test)} "
          f"({int((y_test==0).sum())} normal + {int((y_test==1).sum())} anomaly)")

    if_model = IsolationForestModel(contamination=0.1)
    ae_model = AutoencoderModel(n_components=3)
    svm_model = OneClassSVMModel(nu=0.1)
    if_model.train(X_train)
    ae_model.train(X_train)
    svm_model.train(X_train)
    ensemble = VotingEnsemble()  # (0.35, 0.40, 0.25), threshold 0.5

    def score_all(X):
        s_if = np.array([if_model.score(x) for x in X])
        s_ae = np.array([ae_model.score(x) for x in X])
        s_svm = np.array([svm_model.score(x) for x in X])
        s_ens = np.array([ensemble.vote(a, b, c).weighted_avg_score
                          for a, b, c in zip(s_if, s_ae, s_svm)])
        return {"Isolation Forest": s_if, "PCA Autoencoder": s_ae,
                "One-Class SVM": s_svm, "Ansamblu (vot ponderat)": s_ens}

    val_scores = score_all(X_val)
    test_scores = score_all(X_test)

    # ── Calibrate each model's threshold on validation, evaluate on test ──────
    metrics = {}
    for name in MODEL_NAMES:
        thr, val_f1 = calibrate_threshold(val_scores[name], y_val)
        m = confusion(y_test, (test_scores[name] > thr).astype(int))
        m["roc_auc"] = float(roc_auc_score(y_test, test_scores[name]))
        m["threshold"] = thr
        m["val_f1"] = val_f1
        metrics[name] = m
        print(f"[{name:24s}] thr={thr:.2f} | P={m['precision']:.3f} R={m['recall']:.3f} "
              f"F1={m['f1']:.3f} AUC={m['roc_auc']:.3f} "
              f"(TP={m['TP']} FP={m['FP']} TN={m['TN']} FN={m['FN']})")

    # ── Production default threshold (0.5) on the ensemble, for transparency ──
    ens = test_scores["Ansamblu (vot ponderat)"]
    m05 = confusion(y_test, (ens > DEFAULT_THRESHOLD).astype(int))
    print(f"[ensemble @0.5 (prod default)] P={m05['precision']:.3f} "
          f"R={m05['recall']:.3f} F1={m05['f1']:.3f}")

    # ── Per-anomaly-type recall of the calibrated ensemble ───────────────────
    ens_thr = metrics["Ansamblu (vot ponderat)"]["threshold"]
    ens_pred = (ens > ens_thr).astype(int)
    per_type = {}
    for kind in ANOMALY_TYPES:
        mask = np.array([t == kind for t in types_test])
        det = int(ens_pred[mask].sum())
        per_type[kind] = {"n": int(mask.sum()), "detected": det, "recall": det / int(mask.sum())}
        print(f"[type:{kind:14s}] recall={per_type[kind]['recall']:.3f} ({det}/{int(mask.sum())})")

    # ── Confidence distribution over true anomalies ──────────────────────────
    s_if, s_ae, s_svm = (test_scores["Isolation Forest"], test_scores["PCA Autoencoder"],
                         test_scores["One-Class SVM"])
    conf_counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
    am = y_test == 1
    for a, b, c in zip(s_if[am], s_ae[am], s_svm[am]):
        conf_counts[ensemble.vote(a, b, c).confidence] += 1

    # ── Figures ──────────────────────────────────────────────────────────────
    _plot_roc(test_scores, y_test, metrics)
    _plot_score_dist(ens, y_test, ens_thr)
    _plot_f1_threshold(ens, y_test, ens_thr, metrics["Ansamblu (vot ponderat)"]["f1"])

    results = {
        "config": {
            "seed": SEED, "n_train": N_TRAIN,
            "n_val": int(len(y_val)), "n_test": int(len(y_test)),
            "n_test_normal": N_TEST_NORMAL, "n_test_anomaly": N_TEST_ANOM, "noise": NOISE,
            "weights": {"isolation_forest": DEFAULT_WEIGHTS[0],
                        "autoencoder": DEFAULT_WEIGHTS[1],
                        "one_class_svm": DEFAULT_WEIGHTS[2]},
            "production_threshold": DEFAULT_THRESHOLD,
        },
        "metrics": metrics,
        "ensemble_at_production_threshold_0.5": m05,
        "per_type_recall": per_type,
        "confidence_distribution": conf_counts,
    }
    OUT_JSON.write_text(json.dumps(results, indent=2))
    print(f"[out] wrote {OUT_JSON}")
    print(f"[out] figures in {FIG_DIR}")


def _plot_roc(scores, y_test, metrics):
    plt.figure(figsize=(5.2, 5.0))
    for name in MODEL_NAMES:
        fpr, tpr, _ = roc_curve(y_test, scores[name])
        plt.plot(fpr, tpr, label=f"{name} (AUC={metrics[name]['roc_auc']:.3f})",
                 linewidth=2.2 if name.startswith("Ansamblu") else 1.2)
    plt.plot([0, 1], [0, 1], "k--", linewidth=0.8, label="Aleator")
    plt.xlabel("Rată fals pozitive (FPR)")
    plt.ylabel("Rată adevărat pozitive (TPR)")
    plt.title("Curbe ROC — modele individuale vs. ansamblu")
    plt.legend(loc="lower right", fontsize=8)
    plt.grid(alpha=0.3)
    plt.tight_layout()
    for ext in ("pdf", "png"):
        plt.savefig(FIG_DIR / f"roc.{ext}", dpi=150)
    plt.close()


def _plot_score_dist(s_ens, y_test, thr):
    plt.figure(figsize=(5.6, 4.0))
    bins = np.linspace(0, 1, 40)
    plt.hist(s_ens[y_test == 0], bins=bins, alpha=0.65, label="Normal", color="#2a9d8f")
    plt.hist(s_ens[y_test == 1], bins=bins, alpha=0.65, label="Anomalie", color="#e76f51")
    plt.axvline(thr, color="black", linestyle="--", linewidth=1.3, label=f"Prag calibrat = {thr:.2f}")
    plt.axvline(0.5, color="gray", linestyle=":", linewidth=1.0, label="Prag implicit = 0.50")
    plt.xlabel(r"Scor ponderat al ansamblului $S_{weighted}$")
    plt.ylabel("Număr de exemple")
    plt.title("Distribuția scorurilor: normal vs. anomalie")
    plt.legend(fontsize=8)
    plt.tight_layout()
    for ext in ("pdf", "png"):
        plt.savefig(FIG_DIR / f"score_dist.{ext}", dpi=150)
    plt.close()


def _plot_f1_threshold(s_ens, y_test, best_thr, best_f1):
    grid = np.round(np.arange(0.02, 0.99, 0.01), 2)
    f1s = [confusion(y_test, (s_ens > t).astype(int))["f1"] for t in grid]
    plt.figure(figsize=(5.6, 4.0))
    plt.plot(grid, f1s, color="#264653", linewidth=2)
    plt.axvline(0.5, color="gray", linestyle=":", linewidth=1, label="Prag implicit = 0.50")
    plt.scatter([best_thr], [best_f1], color="#e76f51", zorder=5,
                label=f"Prag calibrat = {best_thr:.2f} (F1={best_f1:.3f})")
    plt.xlabel("Prag de decizie")
    plt.ylabel("F1-score (pe test)")
    plt.title("F1 în funcție de prag (ansamblu)")
    plt.legend(fontsize=8)
    plt.grid(alpha=0.3)
    plt.tight_layout()
    for ext in ("pdf", "png"):
        plt.savefig(FIG_DIR / f"f1_threshold.{ext}", dpi=150)
    plt.close()


if __name__ == "__main__":
    main()
