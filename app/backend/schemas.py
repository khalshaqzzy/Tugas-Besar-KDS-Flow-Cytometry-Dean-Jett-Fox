from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    service: str
    model: str


class DatasetSummary(BaseModel):
    id: str
    name: str
    source_file: str
    condition: str
    timepoint_hours: str
    channel: str
    events_total: int
    events_used: int
    bin_count: int
    csv_path: str


class DatasetsResponse(BaseModel):
    datasets: list[DatasetSummary]


class HistogramInput(BaseModel):
    bins: list[float] = Field(default_factory=list)
    counts: list[float] = Field(default_factory=list)


class InitialParameters(BaseModel):
    g1_mean: float | None = None
    g2_mean: float | None = None


class FitRequest(BaseModel):
    dataset_id: str | None = None
    histogram: HistogramInput | None = None
    initial_parameters: InitialParameters | None = None


class QualityFlag(BaseModel):
    key: str
    severity: str
    label: str
    message: str


class FitResponse(BaseModel):
    fit_id: str
    model_info: dict[str, Any]
    phase_percentages: dict[str, float]
    fit_metrics: dict[str, float | None]
    parameters: dict[str, Any]
    series: dict[str, list[float]]
    warnings: list[str]
    quality_flags: list[QualityFlag]
