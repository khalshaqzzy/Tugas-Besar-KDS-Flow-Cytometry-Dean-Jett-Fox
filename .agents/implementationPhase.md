# Implementation Phase

| Field | Value |
| --- | --- |
| Document status | Active |
| Created | 2026-05-28 |
| Last updated | 2026-05-28 |
| Project | Estimasi Distribusi Fase Siklus Sel dari Data Flow Cytometry Menggunakan Model Dean-Jett-Fox |
| Purpose | Roadmap implementasi dari dataset discovery sampai notebook, API, React virtual lab, laporan, dan video |

## 1. Current State

Repo saat dokumen ini dibuat masih berupa scaffold awal:

- `README.md` berisi judul project.
- `.agents/` berisi PDF spesifikasi tugas, PDF brainstorming, dan dokumen sumber kebenaran.
- Belum ada notebook, dataset, backend, frontend, model reusable, laporan, atau materi presentasi.

Keputusan yang sudah dikunci:

- Bahasa dokumen utama adalah Indonesia.
- Dataset target adalah FCS publik/histogram DNA publik dengan fallback sintetis/CSV kecil.
- Notebook Python adalah artefak ilmiah utama.
- Backend adalah Python FastAPI.
- Frontend adalah Vite React TypeScript.
- Model fitting berjalan di backend/shared Python logic.
- Frontend adalah virtual lab untuk visualisasi dan demo.

## 2. Phase Roadmap

### Phase 0 - Source of Truth dan Scaffold

Status: in progress.

Tujuan:

- membuat `.agents/rules.md`, `.agents/PRD.md`, dan `.agents/implementationPhase.md`;
- menyiapkan struktur folder dasar tanpa mengunci implementasi terlalu dini;
- memperbarui `README.md` dengan ringkasan project dan cara kerja saat scaffold tersedia.

Deliverables:

- dokumen `.agents/` aktif dan konsisten;
- layout awal: `notebooks/`, `data/`, `models/`, `app/backend/`, `app/frontend/`, `reports/`, `presentation/`;
- `.gitkeep` bila direktori kosong perlu dipertahankan;
- README awal yang menjelaskan tujuan dan rencana run command.

Validation:

- tidak ada referensi project template lama tersisa di `.agents/rules.md`;
- PRD menyebut kode Python, laporan maksimal 6 halaman, dan video maksimal 10 menit;
- implementationPhase menyebut semua fase dari dataset sampai final packaging.

### Phase 1 - Dataset Search, Provenance, dan Fallback

Status: pending.

Tujuan:

- menemukan kandidat dataset flow cytometry DNA content/cell cycle;
- mendokumentasikan provenance dataset;
- membuat fallback histogram sintetis/CSV kecil agar pipeline selalu runnable.

Deliverables:

- `data/metadata/dataset_sources.md` atau JSON metadata setara;
- raw dataset bila ukurannya wajar, atau instruksi download bila besar;
- fallback dataset di `data/processed/` atau `data/raw/demo/`;
- script/notebook cell untuk generate fallback dengan seed tetap.

Implementation notes:

- Prioritaskan FlowRepository dan GEO/NCBI.
- Bila memakai FCS, identifikasi channel DNA/fluorescence yang dipakai untuk histogram.
- Bila dataset publik tidak feasible sebelum deadline, catat alasan dan pakai fallback untuk demo.

Validation:

- minimal satu kandidat dataset publik tercatat dengan URL/accession;
- fallback dapat dibaca Python tanpa akses internet;
- metadata membedakan data nyata dan sintetis.

### Phase 2 - Notebook Eksplorasi dan Preprocessing

Status: pending.

Tujuan:

- membuat notebook end-to-end untuk membaca data, membuat histogram, dan memahami distribusi DNA;
- menghasilkan visualisasi awal histogram dan catatan preprocessing.

Deliverables:

- `notebooks/dean_jett_fox_flow_cytometry.ipynb`;
- fungsi preprocessing awal untuk FCS/CSV;
- histogram bins/counts yang disimpan ke `data/processed/`;
- grafik histogram awal untuk laporan.

Implementation notes:

- Gunakan FlowCal atau FlowKit bila FCS dipakai dan dependency berhasil.
- Untuk fallback CSV, gunakan pembacaan pandas/numpy sederhana.
- Notebook harus bisa run all pada fallback tanpa internet.

Validation:

- notebook run all berhasil pada fallback;
- histogram tidak kosong, counts non-negatif, dan bins masuk akal;
- grafik histogram dapat dipakai untuk diskusi awal.

### Phase 3 - Model Dean-Jett-Fox Reusable

Status: pending.

Tujuan:

- memisahkan logic fitting dari notebook agar bisa dipakai backend;
- menghasilkan output model yang stabil untuk notebook dan React virtual lab.

Deliverables:

- module Python model reusable di `models/` atau package backend;
- fungsi utama semacam `fit_dean_jett_fox(bins, counts, initial_parameters=None)`;
- output phase percentages, parameters, metrics, series, warnings;
- unit test untuk fallback dataset.

Implementation notes:

- Gunakan scipy/numpy untuk fitting numerik.
- Constraint parameter harus mencegah amplitude negatif dan `g2_mean <= g1_mean`.
- Hitung residual dan minimal SSE/RMSE; R-squared bila definisinya stabil untuk data.
- Normalisasi proporsi fase ke sekitar 100%.

Validation:

- proporsi G1 + S + G2/M mendekati 100%;
- parameter inti non-negatif;
- fit pada fallback menghasilkan output deterministik;
- warning muncul untuk input invalid atau fit buruk.

### Phase 4 - Backend FastAPI

Status: pending.

Tujuan:

- mengekspos model fitting sebagai API lokal untuk frontend.

Deliverables:

- `app/backend/` dengan FastAPI app;
- endpoint `GET /health`, `GET /datasets`, `POST /fit`;
- schema request/response menggunakan Pydantic;
- loader dataset processed/fallback;
- test API minimal.

Implementation notes:

- Backend tidak boleh bergantung pada notebook state.
- Dataset demo dapat dibaca dari `data/processed/`.
- Error input harus jelas untuk frontend.

Validation:

- `GET /health` mengembalikan status ok;
- `GET /datasets` menampilkan demo dataset;
- `POST /fit` dengan dataset id demo mengembalikan schema sesuai PRD;
- `POST /fit` menolak histogram kosong atau counts negatif.

### Phase 5 - React Virtual Lab

Status: pending.

Tujuan:

- membuat antarmuka visual untuk mendemokan model Dean-Jett-Fox.

Deliverables:

- `app/frontend/` dengan Vite React TypeScript;
- halaman utama virtual lab;
- dataset selector;
- tombol run fit;
- chart histogram, fit total, komponen G1/S/G2-M, residual;
- ringkasan persentase fase dan metrik fit;
- warning/caveat panel.

Implementation notes:

- Gunakan chart library ringan seperti Recharts atau Plotly jika dibutuhkan.
- Fokus pada satu layar kerja yang siap demo, bukan landing page.
- Frontend memanggil backend `/datasets` dan `/fit`.
- Default demo harus bekerja tanpa upload file.

Validation:

- app memuat dataset demo;
- hasil fitting tampil tanpa membaca notebook;
- chart terbaca pada viewport laptop;
- warning dari API tampil di UI.

### Phase 6 - Validasi, Analisis, dan Interpretasi Biologis

Status: pending.

Tujuan:

- memastikan hasil model cukup kuat untuk laporan dan presentasi;
- menulis interpretasi biologis yang jujur terhadap keterbatasan.

Deliverables:

- tabel final proporsi fase;
- grafik final histogram + fit + residual;
- catatan goodness-of-fit;
- bagian diskusi tentang G1, S, G2/M, kualitas dataset, dan batasan model;
- screenshot virtual lab untuk laporan/video bila dibutuhkan.

Implementation notes:

- Jangan mengklaim ground truth bila dataset tidak menyediakan label fase.
- Bandingkan output terhadap ekspektasi biologis umum 2N/4N.
- Jelaskan fallback sintetis bila dipakai.

Validation:

- semua angka final dapat dilacak ke notebook/API;
- grafik final punya label axis, legend, dan caption;
- interpretasi menyebut caveat model dan data.

### Phase 7 - Laporan Ilmiah

Status: pending.

Tujuan:

- membuat laporan maksimal 6 halaman sesuai spesifikasi tugas.

Deliverables:

- draft laporan di `reports/`;
- gambar dan tabel final;
- daftar pustaka;
- tautan kode dan tautan video placeholder/final.

Struktur wajib:

- Pendahuluan: konsep biologi, metode komputasi, tinjauan pustaka, pertanyaan penelitian, tujuan/kontribusi.
- Metode: dataset, preprocessing, model Dean-Jett-Fox, flowchart, komponen program, tautan kode.
- Hasil dan Diskusi: hasil kuantitatif, visualisasi, interpretasi biologis, keterbatasan.
- Kesimpulan: kontribusi objektif dan saran penelitian masa depan.
- Daftar Pustaka.

Validation:

- maksimal 6 halaman;
- menyebut dataset dan fallback secara jujur;
- semua gambar/tabel punya caption;
- link kode dapat diakses evaluator.

### Phase 8 - Video Presentasi dan Final Packaging

Status: pending.

Tujuan:

- menyiapkan demo video maksimal 10 menit dan final submission.

Deliverables:

- outline video di `presentation/`;
- slide singkat;
- script demo program;
- link video final di laporan;
- checklist submission.

Konten video wajib:

- latar belakang masalah;
- metode/algoritma;
- dataset;
- analisis hasil pengujian;
- demo program singkat;
- semua anggota kelompok tampil.

Validation:

- durasi maksimal 10 menit;
- demo berjalan dari notebook atau virtual lab;
- link video ditulis di laporan;
- repo berisi instruksi menjalankan project.

## 3. Recommended First Execution Batch

Batch pertama setelah dokumen ini:

1. Buat scaffold folder minimal dan README awal.
2. Cari dataset publik dan buat `data/metadata/dataset_sources.md`.
3. Buat fallback histogram sintetis kecil dengan seed tetap.
4. Mulai notebook `notebooks/dean_jett_fox_flow_cytometry.ipynb` yang bisa membaca fallback.
5. Implementasikan fungsi model paling kecil yang menghasilkan G1/S/G2-M untuk fallback.

Alasan urutan ini:

- deadline tugas ketat;
- notebook dan hasil analisis lebih penting untuk penilaian daripada polish frontend;
- fallback memastikan demo tidak terblokir dataset eksternal;
- model reusable sejak awal mencegah duplikasi antara notebook dan API.

## 4. Validation Matrix

| Area | Minimum check | Expected result |
| --- | --- | --- |
| Docs | Cari referensi project template lama di `.agents/` | Tidak ada |
| Dataset | Baca fallback CSV/JSON | Bins/counts valid |
| Notebook | Run all fallback | Selesai tanpa internet |
| Model | Fit fallback | Proporsi total sekitar 100% |
| Backend | `GET /health` | Status ok |
| Backend | `POST /fit` demo | Response sesuai PRD |
| Frontend | Load virtual lab | Chart dan fase tampil |
| Report | Page count | Maksimal 6 halaman |
| Video | Duration | Maksimal 10 menit |

## 5. Open Risks

- Dataset publik yang benar-benar cocok dengan DNA content cell cycle mungkin butuh pencarian manual.
- Library FCS dapat memerlukan dependency tambahan dan mungkin lambat di Windows.
- Model Dean-Jett-Fox perlu disederhanakan agar feasible dalam deadline.
- Frontend live fitting bergantung pada backend berjalan lokal.
- Laporan 6 halaman membatasi detail teknis; repo harus menyimpan detail tambahan.

## 6. Definition of Done

Project final dianggap selesai bila:

- repo dapat menjelaskan tujuan dan cara menjalankan project dari README;
- notebook menghasilkan analisis final;
- model fitting reusable tersedia;
- API dan virtual lab demo berjalan lokal;
- laporan ilmiah selesai maksimal 6 halaman;
- video presentasi selesai maksimal 10 menit;
- semua sumber dataset dan fallback terdokumentasi;
- keterbatasan model dan dataset ditulis eksplisit.
