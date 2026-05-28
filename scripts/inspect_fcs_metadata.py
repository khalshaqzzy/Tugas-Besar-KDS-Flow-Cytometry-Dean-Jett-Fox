"""Inspect metadata FCS untuk memilih channel DNA/PI.

Parser ini membaca header dan text segment FCS tanpa dependency eksternal.
Output ditulis ke JSON dan Markdown agar keputusan channel bisa dilacak.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


RAW_DIR = Path("data/raw/zenodo/14928071")
JSON_OUTPUT = Path("data/metadata/zenodo_14928071_fcs_metadata.json")
MD_OUTPUT = Path("data/metadata/zenodo_14928071_fcs_metadata.md")


def parse_header(path: Path) -> dict[str, int | str]:
    with path.open("rb") as handle:
        header = handle.read(58).decode("ascii", errors="replace")

    def read_int(start: int, end: int) -> int:
        value = header[start:end].strip()
        return int(value) if value else 0

    return {
        "version": header[:6],
        "text_start": read_int(10, 18),
        "text_end": read_int(18, 26),
        "data_start": read_int(26, 34),
        "data_end": read_int(34, 42),
        "analysis_start": read_int(42, 50),
        "analysis_end": read_int(50, 58),
    }


def parse_text_segment(path: Path, header: dict[str, int | str]) -> dict[str, str]:
    start = int(header["text_start"])
    end = int(header["text_end"])
    with path.open("rb") as handle:
        handle.seek(start)
        raw = handle.read(end - start + 1).decode("latin-1", errors="replace")

    if not raw:
        return {}

    delimiter = raw[0]
    tokens: list[str] = []
    current: list[str] = []
    i = 1
    while i < len(raw):
        char = raw[i]
        if char == delimiter:
            if i + 1 < len(raw) and raw[i + 1] == delimiter:
                current.append(delimiter)
                i += 2
                continue
            tokens.append("".join(current))
            current = []
        else:
            current.append(char)
        i += 1

    pairs: dict[str, str] = {}
    for index in range(0, len(tokens) - 1, 2):
        key = tokens[index].strip().upper()
        value = tokens[index + 1].strip()
        if key:
            pairs[key] = value
    return pairs


def parameter_table(text: dict[str, str]) -> list[dict[str, Any]]:
    try:
        par_count = int(text.get("$PAR", "0"))
    except ValueError:
        par_count = 0

    rows: list[dict[str, Any]] = []
    for index in range(1, par_count + 1):
        name = text.get(f"$P{index}N", "")
        stain = text.get(f"$P{index}S", "")
        bit_width = text.get(f"$P{index}B", "")
        value_range = text.get(f"$P{index}R", "")
        amplifier = text.get(f"$P{index}E", "")
        combined = f"{name} {stain}".lower()
        score = 0
        for pattern, weight in [
            (r"\bpi\b", 8),
            (r"propidium", 8),
            (r"\bdna\b", 7),
            (r"area|\b-a\b", 2),
            (r"fl2|pe|yl|red", 1),
        ]:
            if re.search(pattern, combined):
                score += weight
        rows.append(
            {
                "index": index,
                "name": name,
                "stain": stain,
                "bit_width": bit_width,
                "range": value_range,
                "amplifier": amplifier,
                "candidate_score": score,
            }
        )
    return rows


def inspect_file(path: Path) -> dict[str, Any]:
    header = parse_header(path)
    text = parse_text_segment(path, header)
    params = parameter_table(text)
    best = max(params, key=lambda row: row["candidate_score"], default=None)
    return {
        "file": path.name,
        "path": str(path.as_posix()),
        "header": header,
        "events": text.get("$TOT"),
        "cytometer": text.get("$CYT") or text.get("$CYTOMETERID"),
        "date": text.get("$DATE"),
        "parameters": params,
        "best_candidate": best,
    }


def render_markdown(results: list[dict[str, Any]]) -> str:
    lines = [
        "# Metadata FCS Zenodo 14928071",
        "",
        "File ini dibuat dari text segment FCS untuk membantu memilih channel DNA/PI.",
        "Pemilihan channel tetap harus diverifikasi dengan histogram dan konteks eksperimen.",
        "",
    ]
    for result in results:
        best = result["best_candidate"] or {}
        lines.extend(
            [
                f"## {result['file']}",
                "",
                f"- Header: `{result['header']['version']}`",
                f"- Events (`$TOT`): {result.get('events') or 'tidak tersedia'}",
                f"- Cytometer: {result.get('cytometer') or 'tidak tersedia'}",
                f"- Kandidat channel DNA/PI otomatis: P{best.get('index', '?')} `{best.get('name', '')}` / `{best.get('stain', '')}`",
                "",
                "| P | `$PnN` | `$PnS` | Range | Bit | Amplifier | Skor kandidat |",
                "| --- | --- | --- | --- | --- | --- | --- |",
            ]
        )
        for row in result["parameters"]:
            lines.append(
                f"| {row['index']} | `{row['name']}` | `{row['stain']}` | {row['range']} | "
                f"{row['bit_width']} | `{row['amplifier']}` | {row['candidate_score']} |"
            )
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    paths = sorted(RAW_DIR.glob("*.fcs"))
    if not paths:
        print(f"Tidak ada file FCS di {RAW_DIR}. Jalankan downloader terlebih dahulu.")
        return 1

    results = [inspect_file(path) for path in paths]
    JSON_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    JSON_OUTPUT.write_text(json.dumps(results, indent=2), encoding="utf-8")
    MD_OUTPUT.write_text(render_markdown(results), encoding="utf-8")

    print(f"Metadata JSON ditulis ke {JSON_OUTPUT}")
    print(f"Metadata Markdown ditulis ke {MD_OUTPUT}")
    for result in results:
        best = result["best_candidate"] or {}
        print(f"{result['file']}: kandidat P{best.get('index', '?')} {best.get('name', '')} / {best.get('stain', '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
