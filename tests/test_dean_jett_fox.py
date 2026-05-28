from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
import pytest


ROOT = Path(__file__).resolve().parents[1]
SUMMARY_PATH = ROOT / "data" / "processed" / "zenodo_14928071_histograms_summary.json"
sys.path.insert(0, str(ROOT))

from models.dean_jett_fox import fit_dean_jett_fox


def load_histograms() -> list[dict]:
    return json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))


def test_fit_dean_jett_fox_returns_stable_schema_for_representative_histogram() -> None:
    item = next(row for row in load_histograms() if row["source_file"] == "Specimen_001_AI_0_001.fcs")

    result = fit_dean_jett_fox(item["bins"], item["counts"])

    assert set(result) == {"model_info", "phase_percentages", "fit_metrics", "parameters", "series", "warnings"}
    assert result["model_info"] == {
        "name": "dean-jett-fox",
        "version": "djf_polynomial_broadened_v2",
    }
    assert set(result["phase_percentages"]) == {"g1", "s", "g2_m"}
    assert {"sse", "rmse", "r_squared", "weighted_sse", "reduced_chi_square"} <= set(result["fit_metrics"])
    assert {
        "g1_mean",
        "g1_sigma",
        "g2_mean",
        "g2_sigma",
        "g1_mean_scaled",
        "g2_mean_scaled",
        "g1_sigma_scaled",
        "g2_sigma_scaled",
        "s_polynomial_coefficients",
        "g2_g1_ratio",
        "g1_cv",
        "debris_area",
    } <= set(result["parameters"])
    assert set(result["series"]) == {
        "bins",
        "observed",
        "fit_total",
        "g1",
        "s",
        "s_unbroadened",
        "g2_m",
        "residual",
        "weighted_residual",
        "debris",
        "background",
    }

    phase_total = sum(result["phase_percentages"].values())
    assert phase_total == pytest.approx(100.0, abs=1e-6)
    assert result["parameters"]["g2_mean"] > result["parameters"]["g1_mean"]
    assert math.isfinite(result["parameters"]["g2_g1_ratio"])
    assert math.isfinite(result["parameters"]["g1_cv"])
    assert result["parameters"]["debris_area"] >= 0
    assert result["parameters"]["g1_sigma"] > 0
    assert result["parameters"]["g2_sigma"] > 0
    assert result["fit_metrics"]["sse"] >= 0
    assert result["fit_metrics"]["rmse"] >= 0
    assert result["fit_metrics"]["weighted_sse"] >= 0
    assert result["fit_metrics"]["reduced_chi_square"] >= 0

    for name, values in result["series"].items():
        assert len(values) == len(item["bins"]), name
        assert all(math.isfinite(float(value)) for value in values), name


def test_fit_dean_jett_fox_handles_all_processed_zenodo_histograms() -> None:
    for item in load_histograms():
        result = fit_dean_jett_fox(item["bins"], item["counts"])

        assert sum(result["phase_percentages"].values()) == pytest.approx(100.0, abs=1e-6)
        assert all(math.isfinite(value) for value in result["phase_percentages"].values())
        assert result["parameters"]["g2_mean"] > result["parameters"]["g1_mean"]
        assert math.isfinite(result["parameters"]["g2_g1_ratio"])
        assert math.isfinite(result["parameters"]["g1_cv"])
        assert math.isfinite(result["fit_metrics"]["weighted_sse"])
        assert math.isfinite(result["fit_metrics"]["reduced_chi_square"])
        assert all(isinstance(warning, str) for warning in result["warnings"])


def test_fit_dean_jett_fox_recovers_synthetic_phase_distribution_with_debris() -> None:
    bins = np.linspace(0.0, 1.0, 220)
    g1 = 7000.0 * np.exp(-0.5 * ((bins - 0.30) / 0.035) ** 2)
    g2 = 2200.0 * np.exp(-0.5 * ((bins - 0.60) / 0.055) ** 2)
    s = np.zeros_like(bins)
    inside = (bins >= 0.30) & (bins <= 0.60)
    t = (bins[inside] - 0.30) / 0.30
    s[inside] = 2700.0 * (0.50 + 0.90 * t + 0.35 * t * t)
    debris = 650.0 * np.exp(-bins / 0.11)
    background = np.full_like(bins, 25.0)
    counts = g1 + s + g2 + debris + background

    result = fit_dean_jett_fox(bins, counts)

    assert result["phase_percentages"]["g1"] == pytest.approx(34.0, abs=15.0)
    assert result["phase_percentages"]["s"] == pytest.approx(49.0, abs=18.0)
    assert result["phase_percentages"]["g2_m"] == pytest.approx(17.0, abs=12.0)
    assert sum(result["phase_percentages"].values()) == pytest.approx(100.0, abs=1e-6)
    assert result["parameters"]["debris_area"] > 0
    assert result["parameters"]["debris_area"] < sum(counts) * 0.35


@pytest.mark.parametrize(
    ("bins", "counts", "match"),
    [
        ([], [], "histogram kosong"),
        ([1.0, 2.0], [1.0], "panjang"),
        ([1.0, 2.0], [1.0, -1.0], "negatif"),
        ([1.0, 2.0], [0.0, 0.0], "semua count nol"),
        ([1.0, float("nan")], [1.0, 2.0], "finite"),
    ],
)
def test_fit_dean_jett_fox_rejects_invalid_histograms(
    bins: list[float],
    counts: list[float],
    match: str,
) -> None:
    with pytest.raises(ValueError, match=match):
        fit_dean_jett_fox(bins, counts)


def test_notebook_markdown_is_written_as_standalone_scientific_report() -> None:
    notebook = json.loads((ROOT / "notebooks" / "dean_jett_fox_flow_cytometry.ipynb").read_text(encoding="utf-8"))
    markdown = "\n".join(
        "".join(cell.get("source", []))
        for cell in notebook["cells"]
        if cell.get("cell_type") == "markdown"
    )
    forbidden_terms = [
        ".agents",
        "fase berikutnya",
        "virtual lab",
        "repo",
        "artefak",
        "ringkasan biologis yang dapat dipakai",
        "untuk laporan",
    ]
    for term in forbidden_terms:
        assert term.lower() not in markdown.lower(), term

    required_terms = [
        "polynomial S phase",
        "broadening",
        "weighted residual",
        "debris",
        "G1",
        "S",
        "G2/M",
        "2N",
        "4N",
        "keterbatasan",
    ]
    for term in required_terms:
        assert term.lower() in markdown.lower(), term
