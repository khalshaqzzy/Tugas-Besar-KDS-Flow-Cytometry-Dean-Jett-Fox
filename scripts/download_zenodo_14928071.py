"""Unduh file FCS prioritas dari Zenodo record 14928071.

Script ini tidak memakai login. File disimpan sebagai raw data dan hanya
divalidasi secara ringan: ukuran minimal, header FCS3.0, dan checksum MD5
dari metadata Zenodo bila tersedia.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


RECORD_ID = "14928071"
API_URL = f"https://zenodo.org/api/records/{RECORD_ID}"
OUTPUT_DIR = Path("data/raw/zenodo/14928071")
MANIFEST_PATH = Path("data/metadata/zenodo_14928071_download_manifest.json")
MIN_BYTES = 1_000_000

PRIORITY_FILES = [
    "Specimen_001_AI_0_001.fcs",
    "Specimen_001_AI_24_002.fcs",
    "Specimen_001_AI_48_003.fcs",
    "Specimen_001_AI_72_004.fcs",
    "Specimen_001_AX_0_005.fcs",
    "Specimen_001_AX_24_006.fcs",
    "Specimen_001_AX_48_007.fcs",
    "Specimen_001_AX_72_008.fcs",
]


def fetch_json(url: str) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"User-Agent": "if3211-djf-downloader/1.0"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def download_file(url: str, target_path: Path) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": "if3211-djf-downloader/1.0"})
    with urllib.request.urlopen(request, timeout=180) as response, target_path.open("wb") as output:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            output.write(chunk)


def md5sum(path: Path) -> str:
    digest = hashlib.md5()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_fcs(path: Path, min_bytes: int, expected_checksum: str | None) -> dict[str, Any]:
    size = path.stat().st_size
    with path.open("rb") as handle:
        header = handle.read(6).decode("ascii", errors="replace")

    actual_md5 = md5sum(path)
    expected_md5 = expected_checksum.removeprefix("md5:") if expected_checksum else None

    checks = {
        "size_bytes": size,
        "header": header,
        "md5": actual_md5,
        "expected_md5": expected_md5,
        "size_ok": size >= min_bytes,
        "header_ok": header == "FCS3.0",
        "md5_ok": expected_md5 is None or actual_md5 == expected_md5,
    }
    checks["ok"] = checks["size_ok"] and checks["header_ok"] and checks["md5_ok"]
    return checks


def main() -> int:
    parser = argparse.ArgumentParser(description="Download FCS prioritas dari Zenodo 14928071.")
    parser.add_argument("--force", action="store_true", help="Unduh ulang walaupun file sudah ada.")
    parser.add_argument("--min-bytes", type=int, default=MIN_BYTES, help="Ukuran minimal file FCS.")
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)

    try:
        record = fetch_json(API_URL)
    except (urllib.error.URLError, TimeoutError) as exc:
        print(f"Gagal mengambil metadata Zenodo: {exc}", file=sys.stderr)
        return 1

    files_by_name = {file_info["key"]: file_info for file_info in record.get("files", [])}
    missing = [name for name in PRIORITY_FILES if name not in files_by_name]
    if missing:
        print(f"File prioritas tidak ditemukan di metadata Zenodo: {missing}", file=sys.stderr)
        return 1

    manifest: dict[str, Any] = {
        "record_id": RECORD_ID,
        "api_url": API_URL,
        "record_url": record.get("links", {}).get("self_html"),
        "doi": record.get("metadata", {}).get("doi"),
        "title": record.get("metadata", {}).get("title"),
        "downloaded_files": [],
    }

    failed = False
    for name in PRIORITY_FILES:
        file_info = files_by_name[name]
        target_path = OUTPUT_DIR / name
        source_url = file_info["links"]["self"]

        if args.force or not target_path.exists():
            print(f"Mengunduh {name} ...")
            try:
                download_file(source_url, target_path)
            except (urllib.error.URLError, TimeoutError) as exc:
                print(f"Gagal mengunduh {name}: {exc}", file=sys.stderr)
                failed = True
                continue
        else:
            print(f"Skip {name}; file sudah ada.")

        checks = validate_fcs(target_path, args.min_bytes, file_info.get("checksum"))
        manifest["downloaded_files"].append(
            {
                "name": name,
                "path": str(target_path.as_posix()),
                "source_url": source_url,
                "zenodo_size_bytes": file_info.get("size"),
                "zenodo_checksum": file_info.get("checksum"),
                **checks,
            }
        )

        if not checks["ok"]:
            failed = True
            print(f"Validasi gagal untuk {name}: {checks}", file=sys.stderr)
        else:
            print(f"OK {name}: {checks['size_bytes']} bytes, {checks['header']}, md5 {checks['md5']}")

    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Manifest ditulis ke {MANIFEST_PATH}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
