# Tugas-Besar-KDS-Flow-Cytometry-Dean-Jett-Fox

Project IF3211 untuk estimasi distribusi fase siklus sel dari data flow cytometry menggunakan model Dean-Jett-Fox.

## Setup

Install dependency Python:

```powershell
python -m pip install -r requirements.txt
```

## Dataset Utama

Dataset utama adalah Zenodo 14928071:

- Record: <https://zenodo.org/records/14928071>
- API metadata: <https://zenodo.org/api/records/14928071>
- DOI: `10.5281/zenodo.14928071`
- Channel awal untuk histogram DNA/PI: `PI-A`

FlowRepository FR-FCM-ZZMY hanya dicatat sebagai dataset sekunder/cadangan karena download raw file membutuhkan login.

## Phase 1-4

Jalankan dari root repo:

```powershell
python scripts\download_zenodo_14928071.py
python scripts\inspect_fcs_metadata.py
python scripts\preprocess_zenodo_histograms.py
```

Notebook analisis:

```text
notebooks/dean_jett_fox_flow_cytometry.ipynb
```

Model reusable:

```python
from models.dean_jett_fox import fit_dean_jett_fox
```

Model default adalah `djf_polynomial_broadened_v2`: G1 dan G2/M sebagai Gaussian berbasis area, S phase sebagai polynomial orde dua dengan broadening, serta komponen debris/background sederhana.

Backend FastAPI:

```powershell
uvicorn app.backend.main:app --reload
```

Endpoint lokal:

- `http://127.0.0.1:8000/health`
- `http://127.0.0.1:8000/datasets`
- `POST http://127.0.0.1:8000/fit`

Contoh request fitting dataset demo:

```json
{
  "dataset_id": "zenodo-14928071-ai-0"
}
```

Validasi:

```powershell
pytest
```

Output fase 1-4 tersimpan di:

- `data/metadata/dataset_sources.md`
- `data/raw/zenodo/14928071/`
- `data/processed/zenodo_14928071_histograms/`
- `data/processed/zenodo_14928071_djf_fit_summary.csv`
- `models/dean_jett_fox.py`
- `app/backend/`
- `tests/test_dean_jett_fox.py`
- `tests/test_backend_api.py`
