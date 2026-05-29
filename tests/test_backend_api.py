from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.backend.main import _scale_initial_parameters, app
from app.backend.quality import build_quality_flags


client = TestClient(app)


def test_health_returns_contract() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "djf-flow-cytometry-api",
        "model": "dean-jett-fox",
    }


def test_datasets_returns_demo_metadata_without_histogram_arrays() -> None:
    response = client.get("/datasets")

    assert response.status_code == 200
    datasets = response.json()["datasets"]
    assert len(datasets) == 8
    assert {item["id"] for item in datasets} == {
        "zenodo-14928071-ai-0",
        "zenodo-14928071-ai-24",
        "zenodo-14928071-ai-48",
        "zenodo-14928071-ai-72",
        "zenodo-14928071-ax-0",
        "zenodo-14928071-ax-24",
        "zenodo-14928071-ax-48",
        "zenodo-14928071-ax-72",
    }
    for item in datasets:
        assert "bins" not in item
        assert "counts" not in item
        assert item["name"].startswith("Zenodo 14928071")
        assert item["channel"] == "PI-A"
        assert item["bin_count"] == 256


def test_fit_with_demo_dataset_returns_model_response() -> None:
    response = client.post("/fit", json={"dataset_id": "zenodo-14928071-ai-0"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["fit_id"] == "zenodo-14928071-ai-0-default"
    assert payload["model_info"]["name"] == "dean-jett-fox"
    assert sum(payload["phase_percentages"].values()) == pytest.approx(100.0, abs=1e-6)
    assert isinstance(payload["warnings"], list)
    assert isinstance(payload["quality_flags"], list)
    assert payload["quality_flags"]
    assert len(payload["series"]["bins"]) == 256
    assert len(payload["series"]["observed"]) == 256
    assert len(payload["series"]["fit_total"]) == 256


def test_initial_parameters_are_scaled_from_raw_bin_units() -> None:
    scaled = _scale_initial_parameters(
        bins=[10.0, 20.0, 30.0],
        initial_parameters={"g1_mean": 20.0, "g2_mean": 30.0},
    )

    assert scaled == {"g1_mean": 0.5, "g2_mean": 1.0}


def test_fit_with_invalid_negative_counts_returns_400() -> None:
    response = client.post(
        "/fit",
        json={
            "histogram": {
                "bins": [1.0, 2.0],
                "counts": [1.0, -1.0],
            }
        },
    )

    assert response.status_code == 400
    assert "negatif" in response.json()["detail"]


def test_fit_requires_exactly_one_input_source() -> None:
    missing = client.post("/fit", json={})
    both = client.post(
        "/fit",
        json={
            "dataset_id": "zenodo-14928071-ai-0",
            "histogram": {
                "bins": [1.0, 2.0],
                "counts": [1.0, 2.0],
            },
        },
    )

    assert missing.status_code == 400
    assert both.status_code == 400
    assert "tepat satu" in missing.json()["detail"]
    assert "tepat satu" in both.json()["detail"]


def test_fit_with_unknown_dataset_id_returns_404() -> None:
    response = client.post("/fit", json={"dataset_id": "zenodo-14928071-missing"})

    assert response.status_code == 404
    assert "dataset_id tidak ditemukan" in response.json()["detail"]


def make_csv(include_header: bool = True, row_count: int = 80) -> str:
    rows = ["bin,count"] if include_header else []
    for index in range(row_count):
        x = index / (row_count - 1)
        g1 = 900.0 * math_exp(-0.5 * ((x - 0.32) / 0.055) ** 2)
        s = 220.0 if 0.32 <= x <= 0.64 else 0.0
        g2 = 320.0 * math_exp(-0.5 * ((x - 0.64) / 0.070) ** 2)
        rows.append(f"{index},{g1 + s + g2 + 4.0:.6f}")
    return "\n".join(rows)


def math_exp(value: float) -> float:
    import math

    return math.exp(value)


def test_fit_csv_accepts_header_csv_upload() -> None:
    response = client.post(
        "/fit/csv",
        files={"file": ("histogram.csv", make_csv().encode("utf-8"), "text/csv")},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["fit_id"] == "uploaded-csv-default"
    assert isinstance(payload["quality_flags"], list)
    assert sum(payload["phase_percentages"].values()) == pytest.approx(100.0, abs=1e-6)
    assert len(payload["series"]["bins"]) == 80


def test_fit_csv_accepts_no_header_csv_and_manual_parameters() -> None:
    response = client.post(
        "/fit/csv",
        data={"g1_mean": "25", "g2_mean": "51"},
        files={"file": ("histogram.csv", make_csv(include_header=False).encode("utf-8"), "text/csv")},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["parameters"]["g2_mean"] > payload["parameters"]["g1_mean"]
    assert len(payload["series"]["observed"]) == 80


def test_fit_csv_short_histogram_does_not_leak_numpy_broadcast_error() -> None:
    response = client.post(
        "/fit/csv",
        data={"g1_mean": "20", "g2_mean": "41"},
        files={"file": ("histogram.csv", make_csv(row_count=64).encode("utf-8"), "text/csv")},
    )

    assert "broadcast" not in response.text
    assert response.status_code == 200
    assert len(response.json()["series"]["bins"]) == 64


@pytest.mark.parametrize(
    ("filename", "content", "match"),
    [
        ("histogram.txt", b"bin,count\n1,2\n2,3\n3,4\n", ".csv"),
        ("histogram.csv", b"bin,count\n1,2\n2,-3\n3,4\n", "negatif"),
        ("histogram.csv", b"bin,count\n1,2\n2,nope\n3,4\n", "non-numeric"),
        ("histogram.csv", b"bin,count\n1,2\n2,3\n", "minimal 3"),
        ("histogram.csv", b"channel,value\n1,2\n2,3\n3,4\n", "header"),
    ],
)
def test_fit_csv_rejects_invalid_uploads(filename: str, content: bytes, match: str) -> None:
    response = client.post(
        "/fit/csv",
        files={"file": (filename, content, "text/csv")},
    )

    assert response.status_code == 400
    assert match in response.json()["detail"]


def test_quality_flags_detect_metric_and_parameter_cautions() -> None:
    flags = build_quality_flags(
        {
            "fit_metrics": {"r_squared": 0.72, "reduced_chi_square": 31.0},
            "parameters": {"g2_g1_ratio": 1.3, "debris_percent_of_total_signal": 24.0},
            "warnings": ["Mean G1 berada dekat batas constraint."],
        }
    )

    keys = {flag["key"] for flag in flags}
    assert {
        "low-r-squared",
        "high-reduced-chi-square",
        "g2-g1-ratio-out-of-range",
        "high-debris",
        "constraint-boundary",
    } <= keys


def test_quality_flags_add_info_when_no_thresholds_are_crossed() -> None:
    flags = build_quality_flags(
        {
            "fit_metrics": {"r_squared": 0.92, "reduced_chi_square": 4.0},
            "parameters": {"g2_g1_ratio": 2.0, "debris_percent_of_total_signal": 3.0},
            "warnings": [],
        }
    )

    assert flags == [
        {
            "key": "fit-review",
            "severity": "info",
            "label": "Tidak ada flag kualitas besar",
            "message": "Metrik utama tidak melewati ambang kehati-hatian yang dikonfigurasi.",
        }
    ]
