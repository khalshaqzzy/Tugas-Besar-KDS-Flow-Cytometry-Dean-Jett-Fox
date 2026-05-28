# Product Requirements Document

| Field | Value |
| --- | --- |
| Document status | Active |
| Created | 2026-05-28 |
| Last updated | 2026-05-28 |
| Project | Estimasi Distribusi Fase Siklus Sel dari Data Flow Cytometry Menggunakan Model Dean-Jett-Fox |
| Course context | IF3211 Domain-Specific Computation |
| Primary artifacts | Notebook Python, React virtual lab, FastAPI model service, laporan ilmiah, video presentasi |

## 1. Ringkasan

Project ini membangun solusi komputasi biologi untuk mengestimasi distribusi fase siklus sel dari data flow cytometry berbasis kandungan DNA. Model Dean-Jett-Fox digunakan untuk memfit histogram DNA dan mengestimasi proporsi sel pada fase G1, S, dan G2/M.

Alur utama project:

1. memakai dan mendokumentasikan dataset flow cytometry publik Zenodo 14928071 sebagai dataset utama;
2. membuat notebook Python end-to-end untuk preprocessing, fitting model, visualisasi, dan analisis;
3. membuat backend FastAPI yang menjalankan fitting model secara reusable;
4. membuat React virtual lab untuk memilih dataset/demo, mengirim data ke backend, dan menampilkan hasil model;
5. menggunakan output notebook dan app untuk laporan ilmiah maksimal 6 halaman dan video demo maksimal 10 menit.

Project tidak bertujuan menjadi alat diagnosis klinis. Semua output harus diposisikan sebagai demonstrasi komputasi biologi dan estimasi berbasis model.

## 2. Latar Belakang

Siklus sel terdiri dari fase G1, S, G2, dan M. Pada pengukuran flow cytometry berbasis DNA content, sel fase G1 umumnya memiliki kandungan DNA 2N, sel fase S berada pada rentang sintesis DNA antara 2N dan 4N, sedangkan sel fase G2/M memiliki kandungan DNA 4N. Distribusi ini penting untuk memahami proliferasi sel, respons terhadap gangguan siklus sel, dan efek perlakuan biologis.

Model Dean-Jett-Fox adalah pendekatan statistik klasik untuk menganalisis histogram DNA flow cytometry. Model ini memisahkan puncak G1 dan G2/M serta memperkirakan kontribusi fase S di antara kedua puncak tersebut. Dalam konteks tugas IF3211, model ini cocok karena menghubungkan konsep biologi siklus sel dengan pemodelan komputasional, fitting numerik, visualisasi data, dan interpretasi hasil.

## 3. Tujuan dan Success Criteria

Tujuan project:

- mendemonstrasikan pemahaman biologi siklus sel melalui model komputasi;
- menghasilkan pipeline Python yang dapat memproses histogram DNA dan mengestimasi proporsi fase;
- menyediakan virtual lab React untuk eksplorasi hasil model secara visual;
- menghasilkan analisis kuantitatif dan kualitatif yang dapat dipakai dalam laporan dan video presentasi.

Success criteria:

- notebook dapat dijalankan dari awal sampai akhir pada dataset publik Zenodo 14928071;
- model menghasilkan estimasi G1, S, dan G2/M yang ternormalisasi dan dapat dijelaskan;
- backend menyediakan endpoint fitting yang stabil;
- frontend menampilkan histogram, kurva fit, residual, proporsi fase, dan warning;
- laporan menjawab pertanyaan penelitian dan menyertakan keterbatasan;
- video menunjukkan latar belakang, metode, dataset, hasil, dan demo program.

## 4. Pertanyaan Penelitian

Pertanyaan utama:

- Bagaimana model Dean-Jett-Fox dapat digunakan untuk mengestimasi proporsi fase G1, S, dan G2/M dari histogram DNA flow cytometry?

Pertanyaan pendukung:

- Seberapa baik kurva fit model mengikuti histogram data berdasarkan residual dan metrik error?
- Bagaimana hasil estimasi fase dapat diinterpretasikan dalam konteks siklus sel?
- Bagaimana preprocessing histogram dan kualitas dataset mempengaruhi hasil estimasi?
- Apa keterbatasan model Dean-Jett-Fox untuk data noisy, overlap puncak, atau dataset yang tidak ideal?

## 5. Target Pengguna

Evaluator:

- dosen dan asisten yang menilai penerapan konsep biologi, metode komputasi, kualitas analisis, laporan, dan presentasi.

Demonstrator:

- anggota kelompok yang menjalankan notebook, menjelaskan model, dan melakukan demo virtual lab dalam video.

Pengguna virtual lab:

- pengguna akademik yang ingin melihat hubungan antara histogram DNA, fitting model, dan estimasi proporsi fase tanpa membaca seluruh notebook.

## 6. Scope

### In Scope

- penggunaan dataset publik Zenodo 14928071 yang relevan dengan DNA content/cell cycle;
- preprocessing FCS/histogram menjadi bins dan counts;
- implementasi fitting Dean-Jett-Fox dalam Python;
- notebook analisis lengkap;
- backend FastAPI untuk menjalankan model;
- React virtual lab untuk visualisasi dan eksplorasi;
- ekspor grafik/tabel hasil untuk laporan;
- dokumentasi provenance dataset dan keterbatasan.

### Out of Scope

- diagnosis klinis atau rekomendasi terapi;
- real-time acquisition dari mesin flow cytometer;
- dukungan penuh untuk semua format, channel, dan protokol flow cytometry;
- sistem authentication, user account, atau database production;
- deployment production jangka panjang;
- klaim akurasi klinis tanpa ground truth dan validasi biologis tambahan.

## 7. Functional Requirements

### 7.1 Dataset Discovery dan Provenance

Sistem/project harus:

- memakai dataset FCS publik Zenodo 14928071 sebagai dataset utama;
- mencatat sumber, accession id, URL, tanggal akses, deskripsi sampel, dan lisensi/ketersediaan;
- mencatat FlowRepository FR-FCM-ZZMY sebagai dataset sekunder/cadangan karena download file mentah membutuhkan login;
- menyediakan script downloader Zenodo tanpa login dan preprocessing histogram `PI-A`.

### 7.2 Notebook Python

Notebook harus:

- menjelaskan konteks biologis dan tujuan analisis;
- membaca dataset publik Zenodo 14928071;
- melakukan preprocessing ke histogram DNA;
- menjalankan fitting model Dean-Jett-Fox;
- menghitung proporsi G1, S, dan G2/M;
- menghitung residual dan metrik goodness-of-fit;
- menghasilkan visualisasi histogram, kurva fit, komponen fase, residual, dan ringkasan persentase;
- menyajikan interpretasi hasil dan keterbatasan.

### 7.3 Model Dean-Jett-Fox

Implementasi model harus:

- menerima histogram `bins` dan `counts`;
- memodelkan komponen G1 dan G2/M sebagai puncak berbasis Gaussian;
- memodelkan fase S sebagai distribusi di antara G1 dan G2/M;
- mengembalikan proporsi fase dalam persen;
- mengembalikan parameter fit yang dapat dilaporkan;
- mencegah atau memberi warning pada parameter tidak valid;
- menghasilkan series visualisasi untuk frontend dan notebook.

### 7.4 Backend API

Backend harus:

- menyediakan API HTTP dengan FastAPI;
- memvalidasi input fitting;
- menjalankan shared model Python;
- mengembalikan response JSON stabil;
- menyediakan daftar dataset demo/processed yang tersedia;
- tidak bergantung pada state notebook.

Endpoint minimum:

- `GET /health`
- `GET /datasets`
- `POST /fit`

### 7.5 React Virtual Lab

Frontend harus:

- menampilkan daftar dataset demo;
- mengizinkan pengguna menjalankan fitting;
- mengizinkan input histogram manual/upload ringan bila feasible;
- menampilkan histogram dan kurva fit;
- menampilkan komponen G1, S, G2/M;
- menampilkan residual;
- menampilkan proporsi fase dalam tabel/kartu ringkas;
- menampilkan warning dan caveat interpretasi;
- menyediakan visual yang cukup jelas untuk demo video.

### 7.6 Laporan dan Video

Project harus mendukung luaran tugas:

- laporan ilmiah maksimal 6 halaman dengan pendahuluan, metode, hasil dan diskusi, kesimpulan, dan daftar pustaka;
- video presentasi maksimal 10 menit yang mencakup latar belakang, metode/algoritma, dataset, hasil pengujian, dan demo program;
- setiap anggota kelompok harus tampil dalam video sesuai spesifikasi tugas.

## 8. API Contract

### `GET /health`

Response:

```json
{
  "status": "ok",
  "service": "djf-flow-cytometry-api",
  "model": "dean-jett-fox"
}
```

### `GET /datasets`

Response:

```json
{
  "datasets": [
    {
      "id": "zenodo-14928071-ai-0",
      "name": "Zenodo 14928071 AI 0h PI-A",
      "source_type": "zenodo_fcs_processed",
      "description": "Histogram PI-A hasil preprocessing FCS Zenodo 14928071.",
      "has_raw_fcs": true,
      "has_processed_histogram": true
    }
  ]
}
```

### `POST /fit`

Request dengan dataset id:

```json
{
  "dataset_id": "zenodo-14928071-ai-0",
  "initial_parameters": {
    "g1_mean": null,
    "g2_mean": null
  }
}
```

Request dengan histogram langsung:

```json
{
  "histogram": {
    "bins": [0, 1, 2],
    "counts": [10, 25, 12]
  },
  "initial_parameters": {
    "g1_mean": null,
    "g2_mean": null
  }
}
```

Response:

```json
{
  "fit_id": "zenodo-14928071-ai-0-default",
  "phase_percentages": {
    "g1": 55.2,
    "s": 26.4,
    "g2_m": 18.4
  },
  "fit_metrics": {
    "sse": 123.4,
    "rmse": 2.1,
    "r_squared": 0.97
  },
  "parameters": {
    "g1_mean": 200.0,
    "g1_sigma": 15.0,
    "g2_mean": 400.0,
    "g2_sigma": 22.0
  },
  "series": {
    "bins": [],
    "observed": [],
    "fit_total": [],
    "g1": [],
    "s": [],
    "g2_m": [],
    "residual": []
  },
  "warnings": []
}
```

## 9. Data dan Model Constraints

- `bins` dan `counts` harus memiliki panjang sama atau bentuk yang terdokumentasi jelas.
- `counts` tidak boleh negatif.
- Histogram kosong harus ditolak.
- Proporsi fase harus dinormalisasi sehingga total mendekati 100%.
- `g2_mean` harus lebih besar dari `g1_mean`.
- Warning harus diberikan bila puncak tidak jelas, fit buruk, atau parameter berada di batas constraint.
- Semua hasil harus reproducible dari raw FCS Zenodo atau histogram processed yang dibuat dari script preprocessing.

## 10. UX Requirements

Virtual lab harus terasa seperti alat eksplorasi akademik:

- tampilan langsung ke workspace analisis, bukan landing page marketing;
- fokus pada dataset, chart, parameter, hasil fase, dan interpretasi;
- grafik harus terbaca untuk presentasi video;
- warning model harus terlihat;
- istilah biologi dan komputasi harus singkat dan jelas;
- desain responsif untuk laptop dan layar presentasi.

## 11. Non-Functional Requirements

- Reproducibility: hasil demo harus bisa diulang.
- Traceability: dataset dan parameter harus bisa dilacak.
- Maintainability: model tidak diduplikasi antara notebook dan API tanpa alasan.
- Performance: fitting demo harus selesai dalam hitungan detik untuk histogram kecil/sedang.
- Robustness: input invalid menghasilkan error message yang jelas.
- Portability: project dapat dijalankan lokal oleh evaluator atau anggota tim.

## 12. Acceptance Criteria

Project dianggap memenuhi MVP bila:

- `.agents/rules.md`, `.agents/PRD.md`, dan `.agents/implementationPhase.md` tersedia dan konsisten;
- notebook utama dapat dijalankan pada dataset Zenodo 14928071;
- sumber dataset publik Zenodo 14928071 telah dicatat, termasuk DOI, file prioritas, manifest download, dan channel kandidat;
- model fitting mengembalikan G1, S, G2/M, metrik fit, dan residual;
- backend API dapat menjalankan `/health`, `/datasets`, dan `/fit`;
- frontend React dapat memuat dataset demo dan menampilkan hasil fitting;
- laporan dapat mengambil grafik/tabel dari notebook atau app;
- video dapat mendemokan notebook atau virtual lab dalam alur yang jelas.

## 13. Risks dan Mitigasi

| Risk | Impact | Mitigasi |
| --- | --- | --- |
| Dataset publik sulit diakses atau tidak sesuai | Analisis data nyata tertunda | Gunakan metadata dan manifest Zenodo untuk re-download; FlowRepository FR-FCM-ZZMY hanya cadangan karena butuh login |
| FCS channel DNA tidak jelas | Histogram tidak valid | Catat channel assumptions dan gunakan dataset/histogram alternatif |
| Model fit buruk pada data noisy | Interpretasi lemah | Tampilkan residual, warning, dan caveat |
| Scope backend/frontend terlalu besar | Deadline terancam | Prioritaskan notebook dan API `/fit` minimal, frontend hanya visualisasi inti |
| Laporan melebihi 6 halaman | Penalti format | Gunakan grafik ringkas dan pindahkan detail teknis ke repo |

## 14. References

- IF3211 Domain-Specific Computation project specification di `.agents/1777454069174_Project-Specification.pdf`.
- Brainstorming topik siklus sel dan Dean-Jett-Fox di `.agents/Brainstorming JUDUL KDS.pdf`.
- Dean PN, Jett JH. Mathematical analysis of DNA distributions derived from flow microfluorometry.
- Fox MH. A model for the computer analysis of synchronous DNA distributions.
- Zenodo 14928071 sebagai dataset utama.
- FlowRepository FR-FCM-ZZMY sebagai dataset sekunder/cadangan karena download file mentah membutuhkan login.
- FlowCal dan FlowKit sebagai kandidat library Python untuk membaca/menangani FCS.
