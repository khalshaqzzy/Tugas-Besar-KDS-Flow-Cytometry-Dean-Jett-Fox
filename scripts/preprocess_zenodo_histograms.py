"""Preprocess FCS Zenodo 14928071 menjadi histogram channel PI-A.

Output CSV di `data/processed/` dipakai sebagai input awal notebook. Script
ini melakukan pembacaan FCS minimal untuk file dengan `$DATATYPE=F` dan
parameter 32-bit, sesuai file prioritas Zenodo 14928071 yang sudah diverifikasi.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

import numpy as np

from inspect_fcs_metadata import parse_header, parse_text_segment


RAW_DIR = Path("data/raw/zenodo/14928071")
OUTPUT_DIR = Path("data/processed/zenodo_14928071_histograms")
SUMMARY_PATH = Path("data/processed/zenodo_14928071_histograms_summary.json")
CHANNEL_NAME = "PI-A"
BIN_COUNT = 256


def read_fcs_events(path: Path) -> tuple[np.ndarray, dict[str, str]]:
    header = parse_header(path)
    text = parse_text_segment(path, header)
    datatype = text.get("$DATATYPE", "").upper()
    byteord = text.get("$BYTEORD", "")
    parameter_count = int(text["$PAR"])
    event_count = int(text["$TOT"])

    bit_widths = [int(text[f"$P{index}B"]) for index in range(1, parameter_count + 1)]
    if datatype != "F" or any(width != 32 for width in bit_widths):
        raise ValueError(f"{path.name}: hanya mendukung $DATATYPE=F dengan semua parameter 32-bit")

    dtype = np.dtype(">f4" if byteord == "4,3,2,1" else "<f4")
    data_start = int(header["data_start"])
    data_end = int(header["data_end"])
    expected_values = event_count * parameter_count

    with path.open("rb") as handle:
        handle.seek(data_start)
        raw = handle.read(data_end - data_start + 1)

    values = np.frombuffer(raw, dtype=dtype, count=expected_values)
    if values.size != expected_values:
        raise ValueError(f"{path.name}: jumlah nilai data tidak sesuai metadata FCS")
    return values.reshape((event_count, parameter_count)), text


def select_channel_index(text: dict[str, str], channel_name: str) -> int:
    parameter_count = int(text["$PAR"])
    for index in range(1, parameter_count + 1):
        if text.get(f"$P{index}N") == channel_name:
            return index - 1
    raise ValueError(f"Channel {channel_name} tidak ditemukan")


def histogram_for_file(path: Path) -> dict[str, Any]:
    events, text = read_fcs_events(path)
    channel_index = select_channel_index(text, CHANNEL_NAME)
    values = events[:, channel_index]
    values = values[np.isfinite(values)]
    values = values[values >= 0]
    if values.size == 0:
        raise ValueError(f"{path.name}: tidak ada nilai valid untuk {CHANNEL_NAME}")

    # Batas histogram memakai percentile agar outlier tetap tidak mendominasi plot awal.
    lower = float(np.percentile(values, 0.5))
    upper = float(np.percentile(values, 99.5))
    if lower >= upper:
        lower = float(values.min())
        upper = float(values.max())

    counts, edges = np.histogram(values, bins=BIN_COUNT, range=(lower, upper))
    centers = (edges[:-1] + edges[1:]) / 2.0

    condition = "AI" if "_AI_" in path.name else "AX" if "_AX_" in path.name else "unknown"
    timepoint = "unknown"
    parts = path.stem.split("_")
    if len(parts) >= 5:
        timepoint = parts[3]

    return {
        "source_file": path.name,
        "condition": condition,
        "timepoint_hours": timepoint,
        "channel": CHANNEL_NAME,
        "events_total": int(text["$TOT"]),
        "events_used": int(values.size),
        "histogram_range": [lower, upper],
        "bin_count": BIN_COUNT,
        "bins": centers.tolist(),
        "counts": counts.astype(int).tolist(),
    }


def write_histogram_csv(item: dict[str, Any]) -> Path:
    output_path = OUTPUT_DIR / f"{Path(item['source_file']).stem}_{item['channel']}_histogram.csv"
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["bin", "count"])
        writer.writerows(zip(item["bins"], item["counts"]))
    return output_path


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    paths = sorted(RAW_DIR.glob("*.fcs"))
    if not paths:
        print(f"Tidak ada file FCS di {RAW_DIR}. Jalankan downloader terlebih dahulu.")
        return 1

    summary: list[dict[str, Any]] = []
    for path in paths:
        item = histogram_for_file(path)
        csv_path = write_histogram_csv(item)
        item["csv_path"] = str(csv_path.as_posix())
        summary.append(item)
        print(
            f"{path.name}: {CHANNEL_NAME}, {item['events_used']} event, "
            f"range {item['histogram_range'][0]:.2f}-{item['histogram_range'][1]:.2f}"
        )

    SUMMARY_PATH.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"Ringkasan histogram ditulis ke {SUMMARY_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
