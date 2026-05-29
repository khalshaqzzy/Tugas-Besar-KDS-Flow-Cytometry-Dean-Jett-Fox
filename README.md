# Tugas-Besar-KDS-Flow-Cytometry-Dean-Jett-Fox

Project IF3211 untuk estimasi distribusi fase siklus sel dari data flow cytometry menggunakan model Dean-Jett-Fox.

## Setup

Prasyarat lokal:

- Node.js dan npm
- `uv` untuk environment Python backend

Install semua dependency dari root repo:

```powershell
npm install
```

## Dataset Utama

Dataset utama adalah Zenodo 14928071:

- Record: <https://zenodo.org/records/14928071>
- API metadata: <https://zenodo.org/api/records/14928071>
- DOI: `10.5281/zenodo.14928071`
- Channel awal untuk histogram DNA/PI: `PI-A`

FlowRepository FR-FCM-ZZMY hanya dicatat sebagai dataset sekunder/cadangan karena download raw file membutuhkan login.

## Workflow Proyek

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

Backend FastAPI dan React virtual lab dapat dijalankan bersama dari root repo:

```powershell
npm run dev
```

Alamat lokal:

- Frontend: `http://127.0.0.1:5173`
- Backend: `http://127.0.0.1:8000`

Endpoint backend:

- `http://127.0.0.1:8000/health`
- `http://127.0.0.1:8000/datasets`
- `POST http://127.0.0.1:8000/fit`
- `POST http://127.0.0.1:8000/fit/csv`

Contoh request fitting dataset demo:

```json
{
  "dataset_id": "zenodo-14928071-ai-0"
}
```

Upload CSV untuk `/fit/csv` memakai multipart form field `file` dengan format `bin,count`, `bins,counts`, atau dua kolom numerik tanpa header. Field opsional `g1_mean` dan `g2_mean` memakai satuan raw bin.

Script root yang tersedia:

```powershell
npm run dev
npm run dev:backend
npm run dev:frontend
npm test
npm run test:backend
npm run test:frontend
```

Frontend memakai `VITE_API_BASE_URL` bila ingin mengganti alamat backend. Default development adalah `http://127.0.0.1:8000`; build production memakai path same-origin `/api`.

Validasi:

```powershell
npm test
npm --prefix app/frontend run build
```

## Deployment Docker Compose

Deployment production berada di folder `deploy/` dan tidak membutuhkan `.env`. Konfigurasi domain, email ACME, dan routing sudah eksplisit di file deployment.

Prasyarat server:

- DNS `djf-demo.khalshaqzzy.site` mengarah ke server deployment
- Port 80 dan 443 terbuka
- Docker dan Docker Compose tersedia

Jalankan dari root repo:

```powershell
docker compose -f deploy/docker-compose.yml up -d --build
```

Caddy akan mengambil sertifikat HTTPS dengan email `khalshaqzzy@gmail.com`. Frontend tersedia di `https://djf-demo.khalshaqzzy.site`, sedangkan backend diproxy pada path `/api`:

- `https://djf-demo.khalshaqzzy.site/api/health`
- `https://djf-demo.khalshaqzzy.site/api/datasets`
- `POST https://djf-demo.khalshaqzzy.site/api/fit`
- `POST https://djf-demo.khalshaqzzy.site/api/fit/csv`

Health check deployment:

```powershell
curl https://djf-demo.khalshaqzzy.site/api/health
```

Output fase 1-5 tersimpan di:

- `data/metadata/dataset_sources.md`
- `data/raw/zenodo/14928071/`
- `data/processed/zenodo_14928071_histograms/`
- `data/processed/zenodo_14928071_djf_fit_summary.csv`
- `models/dean_jett_fox.py`
- `app/backend/`
- `app/frontend/`
- `tests/test_dean_jett_fox.py`
- `tests/test_backend_api.py`
