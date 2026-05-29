"""Reusable Dean-Jett-Fox fitting model.

This module implements a compact Dean-Jett-Fox-style DNA histogram model:
G1 and G2/M are area-normalized Gaussian populations, S phase is a
non-negative quadratic polynomial between both peaks, and the S distribution is
broadened with a Gaussian kernel derived from the G1 coefficient of variation.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import numpy as np
import pandas as pd
from scipy.optimize import least_squares


MODEL_INFO = {"name": "dean-jett-fox", "version": "djf_polynomial_broadened_v2"}


def _as_arrays(bins: Sequence[float], counts: Sequence[float]) -> tuple[np.ndarray, np.ndarray]:
    x = np.asarray(bins, dtype=float)
    y = np.asarray(counts, dtype=float)

    if x.size == 0 or y.size == 0:
        raise ValueError("histogram kosong")
    if x.shape != y.shape:
        raise ValueError("panjang bins dan counts harus sama")
    if x.ndim != 1 or y.ndim != 1:
        raise ValueError("bins dan counts harus berupa array satu dimensi")
    if not np.all(np.isfinite(x)) or not np.all(np.isfinite(y)):
        raise ValueError("bins dan counts harus finite")
    if np.any(y < 0):
        raise ValueError("counts tidak boleh negatif")
    if float(np.sum(y)) <= 0:
        raise ValueError("semua count nol")
    if float(np.max(x) - np.min(x)) <= 0:
        raise ValueError("rentang bins harus lebih dari nol")

    return x, y


def _bin_width(x: np.ndarray) -> float:
    if x.size < 2:
        return 1.0
    return float(np.median(np.diff(np.sort(x))))


def _area_gaussian(x: np.ndarray, area: float, mean: float, sigma: float) -> np.ndarray:
    sigma = max(float(sigma), 1e-9)
    return float(area) / (sigma * np.sqrt(2.0 * np.pi)) * np.exp(-0.5 * ((x - float(mean)) / sigma) ** 2)


def _quadratic_s_phase(
    x: np.ndarray,
    area: float,
    g1_mean: float,
    g2_mean: float,
    c0: float,
    c1: float,
    c2: float,
) -> np.ndarray:
    width = max(float(g2_mean - g1_mean), 1e-9)
    t = (x - float(g1_mean)) / width
    inside = (t >= 0.0) & (t <= 1.0)
    shape = np.zeros_like(x, dtype=float)
    polynomial = float(c0) * (1.0 - t) ** 2 + float(c1) * 2.0 * t * (1.0 - t) + float(c2) * t**2
    shape[inside] = np.clip(polynomial[inside], 0.0, None)
    shape_area = float(np.trapezoid(shape, x))
    if shape_area <= 0:
        return shape
    return shape * (float(area) / shape_area)


def _broaden_component(x: np.ndarray, component: np.ndarray, sigma: float) -> np.ndarray:
    if component.size == 0:
        return component
    step = _bin_width(x)
    sigma_bins = max(float(sigma) / max(step, 1e-9), 0.25)
    radius = max(2, int(np.ceil(4.0 * sigma_bins)))
    offsets = np.arange(-radius, radius + 1, dtype=float)
    kernel = np.exp(-0.5 * (offsets / sigma_bins) ** 2)
    kernel = kernel / kernel.sum()
    broadened_full = np.convolve(component, kernel, mode="full")
    start = max((broadened_full.size - component.size) // 2, 0)
    broadened = broadened_full[start : start + component.size]
    before = float(np.trapezoid(component, x))
    after = float(np.trapezoid(broadened, x))
    if before > 0 and after > 0:
        broadened = broadened * (before / after)
    return broadened


def _debris_component(x: np.ndarray, area: float, decay: float) -> np.ndarray:
    shifted = x - float(x.min())
    decay = max(float(decay), 1e-9)
    shape = np.exp(-shifted / decay)
    shape_area = float(np.trapezoid(shape, x))
    if shape_area <= 0:
        return np.zeros_like(x, dtype=float)
    return shape * (float(area) / shape_area)


def _djf_curve(x: np.ndarray, params: np.ndarray) -> tuple[np.ndarray, dict[str, np.ndarray | float]]:
    (
        g1_area,
        g1_mean,
        g1_sigma,
        g2_area,
        delta,
        g2_sigma,
        s_area,
        s_c0,
        s_c1,
        s_c2,
        debris_area,
        debris_decay,
        baseline,
    ) = params
    g2_mean = g1_mean + delta
    g1 = _area_gaussian(x, g1_area, g1_mean, g1_sigma)
    g2_m = _area_gaussian(x, g2_area, g2_mean, g2_sigma)
    s_unbroadened = _quadratic_s_phase(x, s_area, g1_mean, g2_mean, s_c0, s_c1, s_c2)
    g1_cv = g1_sigma / max(g1_mean, 1e-9)
    s_sigma = np.maximum(g1_cv * np.maximum(x, 1e-9), g1_sigma * 0.40)
    # Use the mean S broadening width for a stable compact implementation.
    s_phase = _broaden_component(x, s_unbroadened, float(np.mean(s_sigma[(x >= g1_mean) & (x <= g2_mean)])) if np.any((x >= g1_mean) & (x <= g2_mean)) else g1_sigma)
    debris = _debris_component(x, debris_area, debris_decay)
    background = np.full_like(x, float(baseline), dtype=float)
    total = g1 + s_phase + g2_m + debris + background
    return total, {
        "g1": g1,
        "s": s_phase,
        "s_unbroadened": s_unbroadened,
        "g2_m": g2_m,
        "debris": debris,
        "background": background,
        "g2_mean": g2_mean,
        "g1_cv": g1_cv,
    }


def _initial_guess(
    x_scaled: np.ndarray,
    counts: np.ndarray,
    initial_parameters: dict[str, float | None] | None,
) -> np.ndarray:
    y_smooth = pd.Series(counts).rolling(window=7, center=True, min_periods=1).mean().to_numpy()
    usable = np.arange(len(x_scaled))
    usable = usable[(x_scaled > 0.05) & (x_scaled < 0.90)]
    peak_idx = usable[np.argmax(y_smooth[usable])] if usable.size else int(np.argmax(y_smooth))
    mu1 = float(x_scaled[peak_idx])
    mu2 = min(0.95, max(mu1 + 0.20, mu1 * 1.9))

    if initial_parameters:
        provided_g1 = initial_parameters.get("g1_mean")
        provided_g2 = initial_parameters.get("g2_mean")
        if provided_g1 is not None:
            mu1 = min(max(float(provided_g1), 0.02), 0.85)
        if provided_g2 is not None:
            mu2 = min(max(float(provided_g2), mu1 + 0.05), 0.95)

    baseline = float(np.percentile(counts, 3))
    signal = np.clip(counts - baseline, 0.0, None)
    total_signal = max(float(np.trapezoid(signal, x_scaled)), 1.0)
    delta = min(max(mu2 - mu1, 0.12), 0.75)
    return np.array(
        [
            total_signal * 0.55,
            min(max(mu1, 0.08), 0.70),
            0.045,
            total_signal * 0.14,
            delta,
            0.060,
            total_signal * 0.31,
            0.80,
            1.10,
            0.80,
            total_signal * 0.03,
            0.08,
            max(baseline, 0.0),
        ],
        dtype=float,
    )


def _to_list(values: np.ndarray) -> list[float]:
    return [float(value) for value in values]


def fit_dean_jett_fox(
    bins: Sequence[float],
    counts: Sequence[float],
    initial_parameters: dict[str, float | None] | None = None,
    options: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Fit a compact Dean-Jett-Fox-style model to a DNA-content histogram."""

    _ = options or {}
    x_raw, y = _as_arrays(bins, counts)
    x_min = float(x_raw.min())
    x_max = float(x_raw.max())
    x_range = max(x_max - x_min, 1e-9)
    x = (x_raw - x_min) / x_range

    p0 = _initial_guess(x, y, initial_parameters)
    lower = np.array([0.0, 0.02, 0.005, 0.0, 0.05, 0.005, 0.0, 0.0, 0.0, 0.0, 0.0, 0.01, 0.0])
    upper = np.array([np.inf, 0.85, 0.25, np.inf, 0.90, 0.30, np.inf, 5.0, 5.0, 5.0, np.inf, 0.40, np.inf])
    weights = np.sqrt(np.maximum(y, 1.0))

    def residual(params: np.ndarray) -> np.ndarray:
        total, _components = _djf_curve(x, params)
        data_residual = (total - y) / weights
        g1_mean = max(float(params[1]), 1e-9)
        g2_mean = float(params[1] + params[4])
        expected_g2_sigma = float(params[2]) * g2_mean / g1_mean
        regularization = 25.0 * np.array(
            [
                (g2_mean / g1_mean - 2.0) / 0.20,
                (float(params[5]) - expected_g2_sigma) / 0.08,
            ],
            dtype=float,
        )
        return np.concatenate([data_residual, regularization])

    result = least_squares(residual, p0, bounds=(lower, upper), max_nfev=9000)
    total, components = _djf_curve(x, result.x)
    residuals = y - total
    weighted_residuals = residuals / weights

    areas = {
        "g1": float(np.trapezoid(components["g1"], x_raw)),
        "s": float(np.trapezoid(components["s"], x_raw)),
        "g2_m": float(np.trapezoid(components["g2_m"], x_raw)),
    }
    positive_areas = {key: max(value, 0.0) for key, value in areas.items()}
    total_area = sum(positive_areas.values())
    phase_percentages = {
        key: positive_areas[key] / total_area * 100.0 if total_area > 0 else 0.0
        for key in ("g1", "s", "g2_m")
    }

    sse = float(np.sum(residuals**2))
    rmse = float(np.sqrt(np.mean(residuals**2)))
    weighted_sse = float(np.sum(weighted_residuals**2))
    degrees_of_freedom = max(int(y.size - result.x.size), 1)
    reduced_chi_square = float(weighted_sse / degrees_of_freedom)
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    r_squared = float(1.0 - sse / ss_tot) if ss_tot > 0 else None

    (
        _g1_area,
        g1_mean_scaled,
        g1_sigma_scaled,
        _g2_area,
        delta_scaled,
        g2_sigma_scaled,
        _s_area,
        s_c0,
        s_c1,
        s_c2,
        _debris_area,
        _debris_decay,
        _baseline,
    ) = [float(value) for value in result.x]
    g2_mean_scaled = g1_mean_scaled + delta_scaled
    g1_mean = x_min + g1_mean_scaled * x_range
    g2_mean = x_min + g2_mean_scaled * x_range
    g1_sigma = g1_sigma_scaled * x_range
    g2_sigma = g2_sigma_scaled * x_range
    g1_cv = float(components["g1_cv"])
    debris_area = float(np.trapezoid(components["debris"], x_raw))
    total_observed_area = float(np.trapezoid(y, x_raw))
    debris_fraction = debris_area / max(total_observed_area, 1e-9)
    g2_g1_ratio = g2_mean / max(g1_mean, 1e-9)

    warnings: list[str] = []
    if not result.success:
        warnings.append("Optimisasi tidak konvergen penuh.")
    if r_squared is not None and r_squared < 0.80:
        warnings.append("R-squared rendah; interpretasi fase perlu hati-hati.")
    if reduced_chi_square > 25.0:
        warnings.append("Reduced chi-square tinggi; residual berbobot masih besar.")
    if g2_g1_ratio < 1.55 or g2_g1_ratio > 2.35:
        warnings.append("Rasio G2/G1 jauh dari ekspektasi 2N/4N.")
    if debris_fraction > 0.20:
        warnings.append("Komponen debris besar; estimasi fase perlu hati-hati.")
    if result.x[4] <= lower[4] + 0.01:
        warnings.append("Jarak G1 dan G2/M berada dekat batas bawah constraint.")
    if result.x[1] <= lower[1] + 0.01 or result.x[1] >= upper[1] - 0.01:
        warnings.append("Mean G1 berada dekat batas constraint.")
    if result.x[2] <= lower[2] + 0.002 or result.x[5] <= lower[5] + 0.002:
        warnings.append("Lebar puncak berada dekat batas bawah constraint.")
    if min(s_c0, s_c1, s_c2) <= 0.03:
        warnings.append("Polynomial S phase berada dekat batas non-negatif.")

    return {
        "model_info": dict(MODEL_INFO),
        "phase_percentages": {key: float(value) for key, value in phase_percentages.items()},
        "fit_metrics": {
            "sse": sse,
            "rmse": rmse,
            "r_squared": r_squared,
            "weighted_sse": weighted_sse,
            "reduced_chi_square": reduced_chi_square,
        },
        "parameters": {
            "g1_mean": g1_mean,
            "g1_sigma": g1_sigma,
            "g2_mean": g2_mean,
            "g2_sigma": g2_sigma,
            "g1_mean_scaled": g1_mean_scaled,
            "g2_mean_scaled": g2_mean_scaled,
            "g1_sigma_scaled": g1_sigma_scaled,
            "g2_sigma_scaled": g2_sigma_scaled,
            "s_polynomial_coefficients": [s_c0, s_c1, s_c2],
            "g2_g1_ratio": g2_g1_ratio,
            "g1_cv": g1_cv,
            "debris_area": debris_area,
            "debris_percent_of_total_signal": debris_fraction * 100.0,
        },
        "series": {
            "bins": _to_list(x_raw),
            "observed": _to_list(y),
            "fit_total": _to_list(total),
            "g1": _to_list(components["g1"]),
            "s": _to_list(components["s"]),
            "s_unbroadened": _to_list(components["s_unbroadened"]),
            "g2_m": _to_list(components["g2_m"]),
            "residual": _to_list(residuals),
            "weighted_residual": _to_list(weighted_residuals),
            "debris": _to_list(components["debris"]),
            "background": _to_list(components["background"]),
        },
        "warnings": warnings,
    }
