# Internals Rules

| Field | Value |
| --- | --- |
| Document status | Active |
| Created | 2026-05-28 |
| Last updated | 2026-05-28 |
| Purpose | Aturan kerja untuk Codex dan kontributor saat membaca, merencanakan, atau mengubah project IF3211 Dean-Jett-Fox Flow Cytometry |

## 1. Mengapa Folder Ini Ada

Folder `.agents/` adalah memori proyek dan sumber kebenaran internal untuk project:

**Estimasi Distribusi Fase Siklus Sel dari Data Flow Cytometry Menggunakan Model Dean-Jett-Fox**.

Folder ini ada untuk:

- menjaga keputusan produk, biologi, komputasi, dan implementasi agar tidak direncanakan ulang;
- menyimpan konteks tugas IF3211 Domain-Specific Computation;
- memastikan notebook, backend Python, dan React virtual lab memakai model dan asumsi yang sama;
- mencatat urutan kerja dari pencarian dataset sampai laporan dan video;
- menjaga sumber PDF tugas dan brainstorming tetap tersedia untuk sesi berikutnya.

`.agents/` tidak boleh dihapus saat cleanup, scaffold ulang, atau reset repo kecuali user secara eksplisit meminta penghapusan `.agents/` by name.

## 2. Source of Truth

### 2.1 Product dan Requirement

Baca `.agents/PRD.md` saat ada ketidakjelasan tentang:

- tujuan penelitian;
- pertanyaan penelitian;
- target pengguna;
- behavior virtual lab;
- model Dean-Jett-Fox yang wajib didukung;
- API contract;
- acceptance criteria;
- batasan dataset dan interpretasi biologis;
- luaran tugas berupa kode Python, laporan ilmiah, dan video presentasi.

### 2.2 Roadmap dan Eksekusi

Baca `.agents/implementationPhase.md` sebelum memulai atau melanjutkan implementasi.

Dokumen tersebut adalah sumber kebenaran untuk:

- fase kerja;
- prioritas implementasi;
- urutan dataset, notebook, model, backend, frontend, laporan, dan video;
- status fase dalam repo terms;
- recommended next work;
- validasi minimum tiap fase.

### 2.3 Sumber Tugas

Sumber tugas yang wajib dipertahankan:

- `.agents/1777454069174_Project-Specification.pdf`
- `.agents/Brainstorming JUDUL KDS.pdf`

Jangan menghapus, mengganti nama, atau memindahkan file PDF ini tanpa instruksi eksplisit.

## 3. Recommended Read Order

Untuk sesi implementasi umum, baca:

1. `.agents/rules.md`
2. `.agents/implementationPhase.md`
3. `.agents/PRD.md`
4. notebook/model/API/frontend files yang relevan
5. `README.md` saat perubahan mempengaruhi onboarding atau cara menjalankan project

Untuk sesi dataset atau notebook, baca:

1. `.agents/rules.md`
2. `.agents/PRD.md`
3. `.agents/implementationPhase.md`
4. metadata dataset di `data/`
5. notebook yang sedang dikerjakan

Untuk sesi frontend/backend, baca:

1. `.agents/rules.md`
2. `.agents/PRD.md`
3. `.agents/implementationPhase.md`
4. shared model atau schema output fitting
5. kode `app/backend/` dan `app/frontend/`

## 4. Repository Layout Rules

Layout target project:

```text
.agents/
app/
  backend/
  frontend/
data/
  raw/
  processed/
  metadata/
models/
notebooks/
reports/
presentation/
tests/
```

Rules:

- Notebook eksplorasi dan pipeline ilmiah utama berada di `notebooks/`.
- Data mentah berada di `data/raw/` dan tidak boleh dimodifikasi in place.
- Data olahan, histogram, dan JSON/CSV hasil preprocessing berada di `data/processed/`.
- Metadata sumber dataset, provenance, lisensi, accession id, link, dan catatan download berada di `data/metadata/`.
- Implementasi model Python reusable berada di `models/` atau package backend yang dapat diimpor notebook dan API.
- Backend runtime berada di `app/backend/`.
- Frontend React runtime berada di `app/frontend/`.
- Laporan ilmiah, gambar final, dan tabel final berada di `reports/`.
- Materi video atau slide presentasi berada di `presentation/`.
- Test lint/unit/integration berada di `tests/` atau folder test lokal masing-masing runtime.

Jika repo belum memiliki layout ini, buat secara bertahap sesuai fase implementasi. Jangan membuat direktori yang tidak diperlukan oleh fase saat ini kecuali untuk menjaga struktur jelas.

## 5. Dataset Rules

Target utama adalah dataset flow cytometry publik dalam format FCS atau data histogram DNA yang dapat dilacak.

Rules:

- Prioritaskan dataset publik dari FlowRepository atau GEO/NCBI yang relevan dengan DNA content/cell cycle.
- Catat setiap sumber dataset di `data/metadata/` dengan accession id, URL, tanggal akses, deskripsi sampel, channel yang dipakai, dan alasan pemilihan.
- Raw FCS atau raw CSV tidak boleh diedit langsung; semua transformasi harus menghasilkan file baru di `data/processed/`.
- Data berukuran besar tidak wajib masuk Git. Jika tidak masuk Git, metadata dan instruksi re-download wajib cukup jelas.
- Fallback sintetis/histogram CSV kecil boleh digunakan untuk demo dan validasi pipeline bila dataset publik tidak tersedia tepat waktu.
- Fallback sintetis harus ditandai jelas sebagai fallback, bukan data eksperimental nyata.
- Laporan wajib menyebutkan apakah hasil utama memakai dataset publik nyata, fallback sintetis, atau kombinasi keduanya.

## 6. Model Dean-Jett-Fox Rules

Model komputasi wajib berfokus pada pemisahan fase siklus sel dari distribusi DNA.

Rules:

- Output fase minimal: G1, S, dan G2/M.
- Komponen G1 dan G2/M dimodelkan sebagai puncak berbasis Gaussian atau pendekatan ekuivalen yang dijelaskan.
- Komponen S dimodelkan sebagai area distribusi antara G1 dan G2/M menggunakan pendekatan Dean-Jett-Fox yang terdokumentasi.
- Hasil fitting wajib mengembalikan persentase fase, parameter model, kurva fit, residual, dan metrik kualitas fit.
- Proporsi fase harus dinormalisasi dan dijelaskan sebagai estimasi, bukan ground truth absolut.
- Parameter yang tidak biologis, seperti amplitude negatif atau posisi G2/M yang tidak masuk akal terhadap G1, harus dicegah atau diberi warning.
- Notebook dan API harus memakai implementasi model yang sama atau shared logic yang jelas.
- Setiap interpretasi biologis harus menyebut caveat kualitas dataset, gating/preprocessing, noise histogram, dan keterbatasan model.

## 7. Backend Rules

Backend Python memegang fitting model dan validasi input.

Rules:

- Backend target adalah FastAPI.
- Endpoint minimum:
  - `GET /health`
  - `GET /datasets`
  - `POST /fit`
- `POST /fit` menerima dataset id atau histogram `bins/counts`, plus parameter awal opsional.
- Response `POST /fit` wajib stabil dan dapat dikonsumsi frontend tanpa parsing ad hoc.
- Backend melakukan validasi panjang array, nilai negatif, data kosong, dan parameter tidak valid.
- Backend tidak boleh bergantung pada state notebook yang sudah dijalankan.
- Backend boleh membaca processed demo dataset dari repo untuk kebutuhan virtual lab.

## 8. Frontend Rules

Frontend React adalah virtual lab untuk eksplorasi visual, bukan sumber utama fitting ilmiah.

Rules:

- Frontend target adalah Vite React TypeScript.
- Frontend memanggil backend untuk menjalankan fitting.
- Frontend menampilkan histogram input, kurva fit total, komponen G1/S/G2-M, residual, persentase fase, dan warning.
- Frontend harus menyediakan sample demo yang dapat dijalankan tanpa user mencari file sendiri.
- Frontend boleh menyediakan kontrol parameter awal, tetapi default harus cukup untuk demo.
- Frontend tidak boleh menyembunyikan warning model atau caveat interpretasi.
- Frontend tidak boleh mengklaim hasil sebagai diagnosis klinis.

## 9. Notebook Rules

Notebook adalah artefak ilmiah utama untuk penilaian kode Python.

Rules:

- Notebook harus dapat dijalankan end-to-end dari dataset/fallback ke tabel dan visualisasi final.
- Notebook harus menjelaskan langkah dataset discovery, preprocessing, histogram generation, fitting, evaluasi, dan interpretasi biologis.
- Notebook harus menghasilkan grafik yang dapat dipakai di laporan dan video.
- Notebook harus memanggil shared model code bila implementasi reusable sudah tersedia.
- Notebook tidak boleh menyimpan secret, token, atau credential.
- Jika memakai dataset besar yang tidak masuk Git, notebook harus tetap runnable dengan fallback demo.

## 10. Documentation Rules

Update `.agents/PRD.md` saat:

- tujuan atau pertanyaan penelitian berubah;
- behavior virtual lab berubah;
- API contract berubah;
- model atau output fitting berubah;
- dataset policy berubah;
- acceptance criteria berubah.

Update `.agents/implementationPhase.md` saat:

- fase selesai atau berubah status;
- urutan kerja berubah;
- blocker baru muncul;
- recommended next work berubah;
- keputusan teknis runtime berubah.

Update `README.md` saat:

- struktur repo berubah;
- setup command tersedia;
- cara menjalankan notebook/backend/frontend berubah;
- project sudah dapat didemo.

## 11. Commit dan Branch Rules

Gunakan conventional commit:

- `docs:` untuk perubahan dokumen;
- `feat:` untuk fitur runtime atau model baru;
- `fix:` untuk bug;
- `test:` untuk test;
- `chore:` untuk maintenance;
- `build:` untuk dependency/build tooling;
- `ci:` untuk workflow.

Subject commit harus singkat, spesifik, dan tidak diakhiri titik.

## 12. Content Rules

Saat menulis `.agents/`:

- tulis untuk future Codex sessions dan kontributor project;
- pisahkan fakta tugas, keputusan project, dan asumsi implementasi;
- jangan menyisipkan klaim ilmiah yang belum dibuktikan oleh notebook;
- jangan menyebut fallback sintetis sebagai dataset nyata;
- catat caveat dan keterbatasan model secara eksplisit;
- gunakan Bahasa Indonesia sebagai bahasa utama dokumen;
- istilah teknis Inggris boleh dipakai bila lebih presisi.

## 13. Frozen Decisions

Jangan re-decide keputusan ini tanpa memperbarui `.agents/PRD.md` dan `.agents/implementationPhase.md`:

- Topik project adalah siklus sel.
- Judul project adalah "Estimasi Distribusi Fase Siklus Sel dari Data Flow Cytometry Menggunakan Model Dean-Jett-Fox".
- Bahasa utama dokumen adalah Indonesia.
- Target luaran mengikuti tugas IF3211: kode Python, laporan ilmiah maksimal 6 halaman, dan video presentasi maksimal 10 menit.
- Notebook Python lengkap adalah artefak ilmiah utama.
- Dataset target adalah FCS publik atau histogram DNA publik, dengan fallback sintetis/CSV kecil untuk demo.
- Backend adalah Python FastAPI.
- Frontend adalah React TypeScript berbasis Vite.
- Model fitting berjalan di backend Python; frontend tidak menjadi implementasi utama model.
- Frontend berperan sebagai virtual lab untuk visualisasi dan eksplorasi.
- Deadline tugas berdasarkan spesifikasi adalah 29 Mei 2026.
