# Tugas-Besar-KDS-Flow-Cytometry-Dean-Jett-Fox

Project IF3211 untuk estimasi distribusi fase siklus sel dari data flow cytometry menggunakan model Dean-Jett-Fox.

## Dataset Utama

Dataset utama adalah Zenodo 14928071:

- Record: <https://zenodo.org/records/14928071>
- API metadata: <https://zenodo.org/api/records/14928071>
- DOI: `10.5281/zenodo.14928071`
- Channel awal untuk histogram DNA/PI: `PI-A`

FlowRepository FR-FCM-ZZMY hanya dicatat sebagai dataset sekunder/cadangan karena download raw file membutuhkan login.

## Phase 1-2

Jalankan dari root repo:

```powershell
python scripts\download_zenodo_14928071.py
python scripts\inspect_fcs_metadata.py
python scripts\preprocess_zenodo_histograms.py
```

Notebook eksplorasi:

```text
notebooks/dean_jett_fox_flow_cytometry.ipynb
```

Output fase 1-2 tersimpan di:

- `data/metadata/dataset_sources.md`
- `data/raw/zenodo/14928071/`
- `data/processed/zenodo_14928071_histograms/`
- `data/processed/zenodo_14928071_djf_fit_summary.csv`
