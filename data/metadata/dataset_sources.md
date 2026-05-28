# Dataset Sources

| Field | Value |
| --- | --- |
| Last updated | 2026-05-28 |
| Project | Estimasi Distribusi Fase Siklus Sel dari Data Flow Cytometry Menggunakan Model Dean-Jett-Fox |
| Course context | IF3211 Domain-Specific Computation |

## Dataset Utama: Zenodo 14928071

- Nama dataset: Raw Flow Cytometry data files for Figures 2A and 2D of the article: A nonenzymatic dependency on inositol-requiring enzyme 1 controls cancer cell cycle progression and tumor growth
- Record URL: <https://zenodo.org/records/14928071>
- API metadata: <https://zenodo.org/api/records/14928071>
- DOI: `10.5281/zenodo.14928071`
- Tipe data: raw flow cytometry dalam format FCS 3.0
- Konteks eksperimen: data flow cytometry cell cycle; konteks artikel/figure terkait menyebut sel di-stain dengan propidium iodide (PI) dan dianalisis berdasarkan DNA content.
- Lokasi raw data lokal: `data/raw/zenodo/14928071/`
- Lokasi metadata lokal:
  - `data/metadata/zenodo_14928071_download_manifest.json`
  - `data/metadata/zenodo_14928071_fcs_metadata.json`
  - `data/metadata/zenodo_14928071_fcs_metadata.md`
- Lokasi histogram hasil preprocessing: `data/processed/zenodo_14928071_histograms/`
- Ringkasan histogram: `data/processed/zenodo_14928071_histograms_summary.json`

### File FCS Prioritas

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

### Alasan Pemilihan

- Dataset tersedia publik dari Zenodo dan file prioritas dapat diunduh melalui API tanpa login.
- File mentah memakai format FCS 3.0 sehingga sesuai dengan target project flow cytometry.
- Metadata FCS menunjukkan channel `PI-A`, `PI-H`, dan `PI-W`; channel `PI-A` dipilih sebagai kandidat utama DNA content karena PI adalah stain yang relevan untuk analisis kandungan DNA dan suffix `-A` umum dipakai untuk sinyal area pada histogram.
- File mencakup dua kondisi (`AI` dan `AX`) serta empat timepoint (0, 24, 48, 72 jam), sehingga mendukung perbandingan distribusi fase siklus sel antar waktu dan kondisi.
- Downloader lokal sudah memverifikasi ukuran minimal, header `FCS3.0`, dan checksum MD5 dari metadata Zenodo.

### Caveat dan Keterbatasan

- Analisis ini adalah analisis komputasi biologi untuk tugas IF3211, bukan analisis klinis.
- Proporsi G1/S/G2-M dari model Dean-Jett-Fox harus diperlakukan sebagai estimasi berbasis histogram, bukan ground truth absolut.
- Pemilihan channel `PI-A` berasal dari metadata FCS dan konteks PI/DNA content; validitas akhir tetap perlu diperiksa lewat bentuk histogram, residual fit, dan goodness-of-fit.
- Data raw FCS tidak boleh diedit langsung. Semua transformasi disimpan sebagai artefak baru di `data/processed/`.
- FCS dapat mengandung debris, doublet, outlier, atau variasi gating yang tidak sepenuhnya ditangani pada fase awal. Preprocessing fase awal hanya membuat histogram channel `PI-A`.

## Dataset Sekunder/Cadangan: FlowRepository FR-FCM-ZZMY

- Status: sekunder/cadangan, tidak digunakan sebagai dataset utama.
- Alasan: akses download file mentah FlowRepository membutuhkan login, sehingga tidak cocok sebagai jalur utama yang harus reproducible tanpa credential.
- Catatan: jangan mengunduh file FlowRepository untuk fase ini. FlowRepository hanya dicatat sebagai kandidat pembanding/cadangan bila akses resmi tersedia di kemudian hari.

## Keputusan Fase 1-2

- Dataset utama project adalah Zenodo 14928071.
- Jalur data cadangan lokal tidak digunakan karena file FCS Zenodo valid dan berhasil diunduh.
- Notebook dan preprocessing diarahkan ke file Zenodo dan histogram `PI-A`.
