# Session Handoff

| Field | Value |
| --- | --- |
| Last updated | 2026-05-28 |
| Repo | `Tugas-Besar-KDS-Flow-Cytometry-Dean-Jett-Fox` |
| Current branch saat handoff dibuat | `main` |
| Project | Estimasi Distribusi Fase Siklus Sel dari Data Flow Cytometry Menggunakan Model Dean-Jett-Fox |
| Course context | IF3211 Domain-Specific Computation |

## Ringkasan Keputusan Terbaru

- Dataset utama project adalah Zenodo 14928071.
- FlowRepository FR-FCM-ZZMY diturunkan menjadi dataset sekunder/cadangan karena raw file membutuhkan login.
- Tidak ada file FlowRepository yang diunduh.
- Tidak ada jalur data buatan pada fase ini karena file FCS Zenodo valid dan dapat diproses.
- Channel DNA/PI awal yang dipakai adalah `PI-A`, berdasarkan metadata FCS yang menunjukkan parameter `PI-A`, `PI-H`, dan `PI-W`.
- Semua output harus diposisikan sebagai analisis komputasi biologi untuk tugas IF3211, bukan klaim klinis.

## Status Fase

### Phase 1 - Dataset Zenodo, Provenance, dan Validasi Raw FCS

Status: selesai.

Evidence:

- File FCS prioritas berhasil diunduh ke `data/raw/zenodo/14928071/`.
- Downloader memverifikasi ukuran minimal, header `FCS3.0`, dan checksum MD5 dari metadata Zenodo.
- Metadata sumber dataset ditulis di `data/metadata/dataset_sources.md`.
- Manifest download ditulis di `data/metadata/zenodo_14928071_download_manifest.json`.
- Metadata FCS ditulis di:
  - `data/metadata/zenodo_14928071_fcs_metadata.json`
  - `data/metadata/zenodo_14928071_fcs_metadata.md`

File FCS prioritas:

| File | Kondisi | Timepoint |
| --- | --- | --- |
| `Specimen_001_AI_0_001.fcs` | AI | 0 jam |
| `Specimen_001_AI_24_002.fcs` | AI | 24 jam |
| `Specimen_001_AI_48_003.fcs` | AI | 48 jam |
| `Specimen_001_AI_72_004.fcs` | AI | 72 jam |
| `Specimen_001_AX_0_005.fcs` | AX | 0 jam |
| `Specimen_001_AX_24_006.fcs` | AX | 24 jam |
| `Specimen_001_AX_48_007.fcs` | AX | 48 jam |
| `Specimen_001_AX_72_008.fcs` | AX | 72 jam |

### Phase 2 - Notebook Eksplorasi dan Preprocessing

Status: selesai.

Evidence:

- Script `scripts/preprocess_zenodo_histograms.py` membuat histogram `PI-A` untuk semua delapan file FCS.
- Histogram tersimpan di `data/processed/zenodo_14928071_histograms/`.
- Ringkasan histogram tersimpan di `data/processed/zenodo_14928071_histograms_summary.json`.
- Notebook `notebooks/dean_jett_fox_flow_cytometry.ipynb` berhasil dieksekusi end-to-end.
- Output fitting awal tersimpan di `data/processed/zenodo_14928071_djf_fit_summary.csv` dan berisi 8 baris.

## Script Penting

- `scripts/download_zenodo_14928071.py`
  - Mengambil metadata dari `https://zenodo.org/api/records/14928071`.
  - Mengunduh delapan file FCS prioritas.
  - Memvalidasi ukuran minimal, header `FCS3.0`, dan checksum MD5.
- `scripts/inspect_fcs_metadata.py`
  - Membaca header dan text segment FCS tanpa dependency FCS eksternal.
  - Membuat JSON dan Markdown metadata channel.
  - Menandai `PI-A` sebagai kandidat utama DNA/PI.
- `scripts/preprocess_zenodo_histograms.py`
  - Membaca data FCS Zenodo.
  - Memakai byte order FCS yang benar untuk file ini.
  - Menghasilkan histogram channel `PI-A` sebanyak 256 bin.

## Cara Reproduksi Phase 1-2

Jalankan dari root repo:

```powershell
python scripts\download_zenodo_14928071.py
python scripts\inspect_fcs_metadata.py
python scripts\preprocess_zenodo_histograms.py
```

Jalankan notebook:

```text
notebooks/dean_jett_fox_flow_cytometry.ipynb
```

Validasi yang sudah dijalankan:

```powershell
python scripts\download_zenodo_14928071.py
$env:PYTHONDONTWRITEBYTECODE='1'; python scripts\preprocess_zenodo_histograms.py
```

Notebook juga sudah dieksekusi via `nbclient` dan selesai tanpa error.

## Hasil Awal Fitting Notebook

File output:

```text
data/processed/zenodo_14928071_djf_fit_summary.csv
```

Catatan:

- Model DJF dalam notebook masih versi eksplorasi fase 2.
- AI 72h menghasilkan warning karena R-squared rendah pada fitting awal.
- Fase 3 harus memindahkan logic fitting ke module reusable dan memperkuat constraint/model selection.

## Caveat Ilmiah

- `PI-A` dipilih berdasarkan metadata dan konteks PI/DNA content; validitas tetap harus dicek lewat histogram, residual, dan goodness-of-fit.
- Preprocessing belum melakukan gating biologis lengkap untuk debris/doublet.
- Proporsi G1/S/G2-M adalah estimasi model, bukan ground truth absolut.
- Jangan membuat klaim diagnosis, terapi, atau klaim klinis.

## Perubahan Dokumen

- `.agents/rules.md` diperbarui agar Zenodo 14928071 menjadi dataset utama.
- `.agents/PRD.md` diperbarui agar requirement dataset dan contoh API mengarah ke Zenodo.
- `.agents/implementationPhase.md` menandai phase 1 dan phase 2 selesai.
- `README.md` berisi alur reproduksi phase 1-2.
- `.gitignore` ditambahkan untuk cache Python, notebook checkpoint, virtualenv, worktree lokal, dan artifact build.

## Catatan Git dan Branch Bersih

- User meminta commit dan push ke `main`.
- User juga meminta branch bersih tanpa history commit, tanpa folder `.agents`, tanpa draft, dan tanpa file yang tidak perlu.
- Branch bersih sebaiknya dibuat sebagai orphan branch dari hasil commit `main`, lalu hanya menyertakan artefak public/submission:
  - `README.md`
  - `.gitignore`
  - `scripts/`
  - `notebooks/`
  - `data/metadata/`
  - `data/processed/`
  - opsional `data/raw/zenodo/14928071/` bila ingin offline runnable tanpa download ulang
- Folder `.agents/` dan `materials/` tidak perlu masuk branch bersih.

## Recommended Next Work

1. Phase 3: pindahkan fungsi fitting Dean-Jett-Fox dari notebook ke module reusable, misalnya `models/dean_jett_fox.py`.
2. Tambahkan test untuk input histogram Zenodo processed.
3. Phase 4: buat FastAPI minimal dengan endpoint `/health`, `/datasets`, dan `/fit`.
4. Phase 5: buat React virtual lab yang membaca dataset processed Zenodo.
5. Phase 6-8: susun grafik final, laporan maksimal 6 halaman, dan video maksimal 10 menit.
