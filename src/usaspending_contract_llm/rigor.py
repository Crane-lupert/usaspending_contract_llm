"""Day-17 statistical rigor: DSR, BH-FDR, cluster bootstrap, Newey-West.

Applies to the §3 main effect (cross-section quintile spread + incremental R²).

References:
- Bailey-de Prado 2014 'Deflated Sharpe Ratio'
- Benjamini-Hochberg 1995 'False Discovery Rate'
- Politis-Romano 1992 'Stationary Bootstrap'
- Newey-West 1987 'Heteroskedasticity & autocorrelation consistent SE'
"""
from __future__ import annotations

import json
import sys

import numpy as np
import pandas as pd
from scipy import stats

from .manifest import DATA_DIR

CROSS_SECTION = DATA_DIR / "cross_section_quintile.json"
OUT = DATA_DIR / "rigor.json"


def deflated_sharpe(sr_observed: float, n_trials: int, n: int) -> dict:
    """Bailey-de Prado DSR.

    Inputs:
        sr_observed: observed Sharpe (annualized).
        n_trials: number of strategies tried (multiplicity correction).
        n: number of observations.
    """
    if n <= 1:
        return {"error": "n<=1", "n": n}
    # Expected max Sharpe under null (Bailey-de Prado eq 2)
    e_max_sr = (1 - np.euler_gamma) * stats.norm.ppf(1 - 1.0 / n_trials) + \
               np.euler_gamma * stats.norm.ppf(1 - 1.0 / (n_trials * np.e))
    sr0 = e_max_sr / np.sqrt(n)
    # DSR p-value (under skew=0, kurt=3 simplification)
    z = (sr_observed - sr0) * np.sqrt(n - 1)
    psr = stats.norm.cdf(z)
    return {
        "sr_observed":   round(sr_observed, 4),
        "n_trials":      n_trials,
        "n":             n,
        "expected_max_sr_null": round(float(e_max_sr), 4),
        "sr_threshold_null":    round(float(sr0), 4),
        "z":             round(float(z), 4),
        "psr":           round(float(psr), 4),
        "dsr_pass_p05":  bool(psr > 0.95),
    }


def bh_fdr(p_values: list[float], q: float = 0.05) -> dict:
    """Benjamini-Hochberg FDR control."""
    if not p_values:
        return {"error": "no_pvals"}
    n = len(p_values)
    sorted_idx = np.argsort(p_values)
    sorted_p = np.array(p_values)[sorted_idx]
    # Largest k such that p_(k) <= (k/n)*q
    crit = q * (np.arange(1, n + 1) / n)
    pass_mask = sorted_p <= crit
    if not pass_mask.any():
        return {"n_tests": n, "n_pass": 0, "alpha_fdr": q, "p_values": p_values}
    k_max = np.where(pass_mask)[0].max() + 1
    return {
        "n_tests":  n,
        "n_pass":   int(k_max),
        "alpha_fdr": q,
        "threshold_p_at_k": float(crit[k_max - 1]),
        "p_values": p_values,
        "rejected": [int(sorted_idx[i]) for i in range(k_max)],
    }


def cluster_bootstrap_t(
    spreads_by_quarter: list[float],
    *,
    B: int = 1000,
    seed: int = 42,
) -> dict:
    """Cluster bootstrap (per-quarter cluster) for spread mean t-stat."""
    if len(spreads_by_quarter) < 4:
        return {"error": "insufficient_quarters", "n": len(spreads_by_quarter)}
    rng = np.random.RandomState(seed)
    a = np.array(spreads_by_quarter)
    obs_mean = a.mean()
    obs_t = obs_mean / (a.std(ddof=1) / np.sqrt(len(a))) if a.std(ddof=1) > 0 else float("nan")
    boot_means: list[float] = []
    for _ in range(B):
        idx = rng.randint(0, len(a), size=len(a))
        sample = a[idx]
        boot_means.append(sample.mean())
    boot_means_arr = np.array(boot_means)
    se = boot_means_arr.std(ddof=1)
    ci_low, ci_high = np.percentile(boot_means_arr, [2.5, 97.5])
    return {
        "n_quarters":  len(a),
        "obs_mean":    round(float(obs_mean), 6),
        "obs_t":       round(float(obs_t), 4),
        "boot_se":     round(float(se), 6),
        "boot_ci95":   [round(float(ci_low), 6), round(float(ci_high), 6)],
        "boot_excludes_zero": bool(ci_low > 0 or ci_high < 0),
    }


def newey_west_se(spreads: list[float], lags: int = 4) -> dict:
    """Newey-West HAC SE for the mean of `spreads`."""
    if len(spreads) < lags + 2:
        return {"error": "insufficient_data", "n": len(spreads)}
    a = np.array(spreads)
    n = len(a)
    mu = a.mean()
    e = a - mu
    gamma_0 = np.sum(e * e) / n
    nw = gamma_0
    for k in range(1, lags + 1):
        gamma_k = np.sum(e[:-k] * e[k:]) / n
        w = 1 - k / (lags + 1)
        nw += 2 * w * gamma_k
    se = np.sqrt(nw / n) if nw > 0 else float("nan")
    t_nw = mu / se if se > 0 else float("nan")
    return {
        "n":          n,
        "lags":       lags,
        "mean":       round(float(mu), 6),
        "nw_variance": round(float(nw), 6),
        "nw_se":      round(float(se), 6),
        "nw_t":       round(float(t_nw), 4),
    }


def main() -> int:
    if not CROSS_SECTION.exists():
        print("ERR: cross_section_quintile.json missing")
        return 1
    j = json.loads(CROSS_SECTION.read_text(encoding="utf-8"))
    s = j.get("spread_summary", {})
    rows = s.get("rows", [])
    spreads = [r["spread"] for r in rows if r.get("spread") is not None]
    sharpe_a = s.get("sharpe_annualized", 0.0)
    n_q = s.get("n_quarters", 0)

    out = {
        "deflated_sharpe":    deflated_sharpe(sharpe_a, n_trials=9, n=n_q) if n_q > 1 else {"error": "n<=1"},
        "newey_west_lag4":    newey_west_se(spreads, lags=4),
        "cluster_bootstrap":  cluster_bootstrap_t(spreads, B=1000),
        "bh_fdr_n9":          bh_fdr([0.05, 0.01, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80], q=0.05),  # placeholder; real p-values come from §3 tests
        "bh_fdr_note":        "Replace placeholder with actual p-values from §3.1 incremental R² + §3.2 quintile spread + §3.3 ROC-AUC across 3 axes / 3 horizons.",
    }
    OUT.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    print(json.dumps(out, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
