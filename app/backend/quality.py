from __future__ import annotations

from typing import Any, Literal


Severity = Literal["info", "caution", "warning"]


def _flag(key: str, severity: Severity, label: str, message: str) -> dict[str, str]:
    return {
        "key": key,
        "severity": severity,
        "label": label,
        "message": message,
    }


def build_quality_flags(result: dict[str, Any]) -> list[dict[str, str]]:
    metrics = result.get("fit_metrics", {})
    parameters = result.get("parameters", {})
    warnings = result.get("warnings", [])
    flags: list[dict[str, str]] = []

    r_squared = metrics.get("r_squared")
    if r_squared is not None and r_squared < 0.80:
        flags.append(
            _flag(
                "low-r-squared",
                "warning",
                "R-squared rendah",
                "R-squared berada di bawah 0,80 sehingga kurva hasil fitting hanya menjelaskan sebagian variasi histogram.",
            )
        )

    reduced_chi_square = metrics.get("reduced_chi_square")
    if reduced_chi_square is not None and reduced_chi_square > 25.0:
        flags.append(
            _flag(
                "high-reduced-chi-square",
                "warning",
                "Reduced chi-square tinggi",
                "Residual berbobot masih besar; tinjau grafik residual sebelum menafsirkan estimasi fase.",
            )
        )

    g2_g1_ratio = parameters.get("g2_g1_ratio")
    if g2_g1_ratio is not None and (g2_g1_ratio < 1.55 or g2_g1_ratio > 2.35):
        flags.append(
            _flag(
                "g2-g1-ratio-out-of-range",
                "caution",
                "Rasio G2/G1 di luar rentang",
                "Mean G2/M hasil fitting cukup jauh dari relasi 2N/4N yang diharapkan terhadap G1.",
            )
        )

    debris_percent = parameters.get("debris_percent_of_total_signal")
    if debris_percent is not None and debris_percent > 20.0:
        flags.append(
            _flag(
                "high-debris",
                "caution",
                "Sinyal debris tinggi",
                "Komponen debris melebihi 20% dari sinyal teramati sehingga estimasi fase perlu dibaca dengan hati-hati.",
            )
        )

    for warning in warnings:
        warning_text = str(warning)
        if "constraint" in warning_text or "batas" in warning_text:
            flags.append(
                _flag(
                    "constraint-boundary",
                    "caution",
                    "Parameter dekat constraint",
                    "Setidaknya satu parameter hasil fitting berada dekat batas constraint model.",
                )
            )
            break

    if not flags:
        flags.append(
            _flag(
                "fit-review",
                "info",
                "Tidak ada flag kualitas besar",
                "Metrik utama tidak melewati ambang kehati-hatian yang dikonfigurasi.",
            )
        )

    return flags
