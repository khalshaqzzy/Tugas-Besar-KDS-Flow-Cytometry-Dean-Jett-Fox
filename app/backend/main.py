from __future__ import annotations

from collections.abc import Sequence
from typing import Annotated
from typing import Any

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app.backend.csv_histograms import parse_histogram_csv
from app.backend.datasets import DatasetNotFoundError, get_histogram_by_id, list_dataset_summaries
from app.backend.quality import build_quality_flags
from app.backend.schemas import DatasetsResponse, FitRequest, FitResponse, HealthResponse
from models.dean_jett_fox import fit_dean_jett_fox


app = FastAPI(title="DJF Flow Cytometry API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "https://djf-demo.khalshaqzzy.site",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _scale_initial_parameters(
    bins: Sequence[float],
    initial_parameters: dict[str, float | None] | None,
) -> dict[str, float | None] | None:
    if not initial_parameters:
        return None
    values = [float(value) for value in bins]
    if not values:
        return initial_parameters
    x_min = min(values)
    x_range = max(values) - x_min
    if x_range <= 0:
        return initial_parameters

    scaled: dict[str, float | None] = {}
    for key in ("g1_mean", "g2_mean"):
        raw_value = initial_parameters.get(key)
        scaled[key] = None if raw_value is None else (float(raw_value) - x_min) / x_range
    return scaled


def _initial_parameters_from_request(request: FitRequest) -> dict[str, float | None] | None:
    if request.initial_parameters:
        if hasattr(request.initial_parameters, "model_dump"):
            return request.initial_parameters.model_dump()
        return request.initial_parameters.dict()
    return None


def _fit_histogram(
    fit_id: str,
    bins: Sequence[float],
    counts: Sequence[float],
    initial_parameters: dict[str, float | None] | None = None,
) -> FitResponse:
    scaled_initial = _scale_initial_parameters(bins, initial_parameters)
    try:
        result = fit_dean_jett_fox(bins, counts, initial_parameters=scaled_initial)
    except ValueError as exc:
        detail = str(exc)
        if "broadcast" in detail:
            detail = "fitting gagal karena ukuran komponen model tidak konsisten dengan histogram; gunakan CSV yang valid atau parameter awal yang lebih wajar"
        raise HTTPException(status_code=400, detail=detail) from exc
    result["quality_flags"] = build_quality_flags(result)
    return FitResponse(fit_id=fit_id, **result)


def _fit_response(fit_id: str, bins: Sequence[float], counts: Sequence[float], request: FitRequest) -> FitResponse:
    return _fit_histogram(fit_id, bins, counts, _initial_parameters_from_request(request))


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", service="djf-flow-cytometry-api", model="dean-jett-fox")


@app.get("/datasets", response_model=DatasetsResponse)
def datasets() -> DatasetsResponse:
    return DatasetsResponse(datasets=list_dataset_summaries())


@app.post("/fit", response_model=FitResponse)
def fit(request: FitRequest) -> FitResponse:
    has_dataset = request.dataset_id is not None
    has_histogram = request.histogram is not None
    if has_dataset == has_histogram:
        raise HTTPException(status_code=400, detail="request harus berisi tepat satu dari dataset_id atau histogram")

    if request.dataset_id is not None:
        try:
            row = get_histogram_by_id(request.dataset_id)
        except DatasetNotFoundError as exc:
            raise HTTPException(status_code=404, detail=f"dataset_id tidak ditemukan: {request.dataset_id}") from exc
        return _fit_response(
            fit_id=f"{request.dataset_id}-default",
            bins=row["bins"],
            counts=row["counts"],
            request=request,
        )

    if request.histogram is None:
        raise HTTPException(status_code=400, detail="histogram wajib diisi bila dataset_id tidak dipakai")

    return _fit_response(
        fit_id="custom-histogram-default",
        bins=request.histogram.bins,
        counts=request.histogram.counts,
        request=request,
    )


@app.post("/fit/csv", response_model=FitResponse)
async def fit_csv(
    file: Annotated[UploadFile, File(...)],
    g1_mean: Annotated[float | None, Form()] = None,
    g2_mean: Annotated[float | None, Form()] = None,
) -> FitResponse:
    content = await file.read()
    try:
        bins, counts = parse_histogram_csv(content, filename=file.filename)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    initial_parameters = {"g1_mean": g1_mean, "g2_mean": g2_mean}
    return _fit_histogram("uploaded-csv-default", bins, counts, initial_parameters)
