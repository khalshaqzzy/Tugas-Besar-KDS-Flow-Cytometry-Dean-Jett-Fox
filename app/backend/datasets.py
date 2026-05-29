from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
SUMMARY_PATH = ROOT / "data" / "processed" / "zenodo_14928071_histograms_summary.json"


class DatasetNotFoundError(KeyError):
    """Raised when a requested demo dataset id is not available."""


def dataset_id_for(row: dict[str, Any]) -> str:
    condition = str(row["condition"]).lower()
    timepoint = str(row["timepoint_hours"]).lower().replace(" ", "-")
    return f"zenodo-14928071-{condition}-{timepoint}"


def _dataset_name(row: dict[str, Any]) -> str:
    return f"Zenodo 14928071 {row['condition']} {row['timepoint_hours']}h {row['channel']}"


@lru_cache(maxsize=1)
def load_histogram_rows() -> tuple[dict[str, Any], ...]:
    rows = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
    return tuple(rows)


def list_dataset_summaries() -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []
    for row in load_histogram_rows():
        summaries.append(
            {
                "id": dataset_id_for(row),
                "name": _dataset_name(row),
                "source_file": row["source_file"],
                "condition": row["condition"],
                "timepoint_hours": str(row["timepoint_hours"]),
                "channel": row["channel"],
                "events_total": int(row["events_total"]),
                "events_used": int(row["events_used"]),
                "bin_count": int(row["bin_count"]),
                "csv_path": row["csv_path"],
            }
        )
    return summaries


def get_histogram_by_id(dataset_id: str) -> dict[str, Any]:
    for row in load_histogram_rows():
        if dataset_id_for(row) == dataset_id:
            return row
    raise DatasetNotFoundError(dataset_id)
