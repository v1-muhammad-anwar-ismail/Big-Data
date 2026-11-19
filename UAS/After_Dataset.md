# Panduan Langkah Selanjutnya Pasca-Crawling Dataset (`After_Dataset`)

Dokumen ini merupakan lanjutan dari [Analisis.md](./Analisis.md) sebagai acuan operasional bagi kelompok (**Muhammad Anwar Ismail, Ramzi, dan Shobrun**) setelah tahap awal pengumpulan data menggunakan **JinwooCrawl** selesai, agar seluruh tahapan implementasi **HDFS $\rightarrow$ Apache Spark $\rightarrow$ Spark MLlib $\rightarrow$ Draf Artikel Ilmiah** berjalan sesuai [Panduan Proyek Akhir Big Data 2026.pdf](./Panduan%20Proyek%20Akhir%20Big%20Data%202026.pdf).

---

## 1. Pengingat Fondasi Diskusi Ramzi & Shobrun

Agar pengerjaan tetap satu arah dengan konsep yang sudah disepakati bersama:

1. **Topik & Landasan Ilmiah (Usulan Shobrun):**
   * Mengangkat tema **Issue Attention Cycle** (**Anthony Downs, 1972**): memetakan siklus umur suatu isu di ruang publik digital mulai dari kemunculan, puncak viral (*peak*), pembahasan berulang, hingga meredup (*decay*).
   * **Permasalahan & Algoritma Spark MLlib:**
     * **Klasifikasi:** memprediksi kategori durasi/intensitas sorotan isu (cepat reda vs menengah vs berkelanjutan) dengan `RandomForestClassifier`, `LogisticRegression`, atau `NaiveBayes`.
     * **Regresi:** mengestimasi lama hari bertahan atau tingkat atensi/engagement isu dengan `GBTRegressor` atau `LinearRegression`.
2. **Validasi Legalitas, Teknis & Roadmap (Sintesis ChatGPT Ramzi + Shobrun):**
   * **Ramzi:** Memastikan pengumpulan data publik media massa & media sosial untuk riset akademik diperbolehkan menurut **UU No. 27 Tahun 2022 (UU PDP)** selama tidak mengekspos data privat sensitif, serta memvalidasi GDELT 2.0 gratis tanpa API key.
   * **Shobrun:** Menegaskan alur bertahap yang disiplin: **pastikan dataset mentah (JSON/CSV) valid & bersih terlebih dahulu di tahap Python sebelum masuk ke Hadoop HDFS, Spark SQL, Spark MLlib, eksperimen skala data, dan penulisan artikel**.

---

## 2. Audit Kondisi Dataset Saat Ini

Hasil pemeriksaan langsung terhadap ekspor awal [`jinwoo_crawl_dataset.csv`](./jinwoo_crawl_dataset.csv) dan [`jinwoo_crawl_dataset.json`](./jinwoo_crawl_dataset.json):

| Aspek Pemeriksaan | Hasil Aktual di Dataset | Catatan Evaluasi |
| :--- | :--- | :--- |
| **Total Baris & Ukuran** | `20.184` baris (`CSV`: `5,47 MB`, `JSON`: `24,47 MB`) | Sudah memenuhi syarat minimum `> 20.000` baris pada Panduan hal. 3 |
| **Kebersihan Teknis** | `0` nilai kosong (*null*), `20.184` URL unik | Bebas duplikat URL (`canonical_url` + `content_hash`) |
| **Kata Kunci (`keyword`)** | **`GTA 6 rilis` (`20.184` baris / 100%)** | **Baru 1 topik.** Perlu ditambah topik pembanding agar variasi kurva & label MLlib kaya |
| **Sebaran Platform** | YouTube: `19.997` (`497` video + `19.500` komentar)<br>News (GDELT/ID): `127`<br>TikTok (`pyktok`+`tiktok_api`): `46`<br>Facebook: `14` \| Instagram: `0` | Mayoritas berasal dari YouTube API karena kuota resmi besar; Instagram `0` untuk topik ini perlu dilengkapi atau dicatat di keterbatasan riset |
| **Rentang Waktu** | `2021-03-12` s.d. `2026-11-19` (`2026`: `16.456` baris) | Puncak November 2026 terlihat jelas: `2026-11-10` (`1.003` baris) & `2026-11-18` (`999` baris) |
| **Skor Sentimen (`sentiment_tone`)** | Hanya `89` dari `20.184` baris bernilai $\ne 0$ | Kamus sentimen scraper bawaan berfokus pada kata bencana/politik ID; **wajib dihitung ulang di PySpark** berbasis `content`/`title` |

---

## 3. Gunakan JSON atau CSV, dan Apa Saja yang Dibandingkan?

### A. Pilihan Format Utama untuk HDFS & Spark
* **Jadikan `.json` (`jinwoo_crawl_dataset.json`) sebagai sumber utama di HDFS & Spark** (sedangkan `.csv` tetap disimpan sebagai ringkasan tabular ringan).
* Alasannya, file `.json` memuat 3 komponen penting yang **tidak ada** di `.csv`:
  1. **`content`**: teks lengkap berita, caption, dan komentar untuk ekstraksi fitur teks (**Tokenizer + TF-IDF**) serta perhitungan sentimen ulang di PySpark.
  2. **`published_at`**: timestamp presisi hingga jam-menit-detik UTC (mis. `2026-11-17T09:00:08Z`) untuk mengukur fase awal **24–48 jam**.
  3. **`raw_data.type` & `raw_data.video_id`**: penanda untuk membedakan konten/berita induk (`video`, post medsos, artikel berita) vs respons diskusi (`comment`).

> [!TIP]
> Karena `jinwoo_crawl_dataset.json` berbentuk **JSON Array** (`[...]`), pembacaan di PySpark nantinya memakai `.option("multiLine", "true").json(...)` atau dikonversi lebih dulu menjadi **JSON Lines (NDJSON)** / **Parquet** sebelum atau saat pemrosesan Spark.

### B. Matriks Variabel Perbandingan Antar 5 Keyword

| Dimensi Perbandingan | Sumber Field (`JSON` / `CSV`) | Analisis di Spark SQL & MLlib |
| :--- | :--- | :--- |
| **Kurva Volume & Umur Atensi** | `keyword`, `published_date`, `published_at` | Volume postingan per hari/minggu, hari puncak (*peak*), jumlah hari aktif, & *Decay Rate* ($3$–$7$ hari pasca-puncak) |
| **Ledakan Fase Awal (`early_volume`)** | `keyword`, `published_at` | Banyaknya unggahan & komentar dalam $24$–$48$ jam pertama gelombang pembahasan |
| **Engagement & Rasio Diskusi** | `metrics.views`, `likes`, `comments`, `shares`, `raw_data.type` | Rata-rata interaksi per publikasi (khusus baris non-komentar) serta rasio diskusi (`total comment / total post`) |
| **Diversitas Sumber Media** | `author_or_source`, `platform`, `tool_source` | Jumlah kanal/media unik (*unique_media_count*) untuk melihat apakah isu tersebar luas atau hanya terpusat di beberapa akun |
| **Polaritas Sentimen & Konten Teks** | `title`, `content`, `category` | Hitung ulang skor sentimen + fitur TF-IDF di Spark untuk menguji korelasi nada kontroversial/negatif dengan panjang umur isu |

---

## 4. Sebaiknya Pakai Semuanya atau Sebagian Data Agar Kurva Valid?

**Kesimpulan metodologi: Masukkan SEMUA data ke HDFS untuk skala Big Data & eksperimen runtime, tetapi PISAHKAN, SELARASKAN JENDELA WAKTU, dan NORMALISASI di dalam Spark SQL saat membentuk kurva.**

Agar kurva perbandingan 5 keyword **valid secara ilmiah** (tidak menipu akibat efek teknis scraping), terapkan **3 aturan wajib** berikut di PySpark:

1. **Pisahkan Konten Induk (`type != 'comment'`) vs Komentar (`type == 'comment'`)**
   * Di dataset `'GTA 6 rilis'`, terdapat `497` video + `127` berita + `46` TikTok + `14` Facebook (= `684` publikasi induk) dan `19.500` komentar netizen (`views = 0`).
   * Jika digabung mentah, rata-rata `views` jatuh drastis karena tertarik oleh `19.500` komentar bernilai `views = 0`.
   * Solusinya, sajikan dua kurva yang jelas maknanya di Spark SQL:
     * **Kurva *Creator/Media Supply*:** agregasi harian khusus publikasi induk.
     * **Kurva *Public Discourse*:** agregasi harian seluruh diskusi & komentar.
2. **Pakai Jendela Waktu Sejajar (*Aligned Time Window*) — Bukan 5 Tahun Mentah**
   * Pada `'GTA 6 rilis'`, sebaran 2021–2026 sangat berat ke akhir tahun 2026 (`2021`: `10` data vs `2026`: `16.456` data) akibat *recency bias* bawaan API pencarian YouTube/TikTok.
   * Sebaliknya, pada rentang aktif **14–30 hari terakhir** (`2026-11`), kurva siklus atensi terlihat nyata (`2026-11-06`–`08`: `71`–`74`/hari $\rightarrow$ puncak `#1` `2026-11-10`: `1.003` $\rightarrow$ mereda `187`–`223` $\rightarrow$ puncak `#2` `2026-11-18`: `999`).
   * Untuk perbandingan 5 keyword agar adil: gunakan **rentang jendela waktu yang sama** (mis. 14–30 hari terakhir) **atau** sejajarkan pada **hari relatif $t = 0$ (hari puncak masing-masing isu)**. Analisis jangka panjang `2021–2026` dipakai terpisah khusus untuk artikel berita/video historis.
3. **Seimbangkan Kuota atau Normalisasi Proporsi Antar Keyword**
   * Jangan membandingkan angka absolut mentah antara keyword berjumlah `20.184` baris vs keyword lain yang hanya `3.000` baris.
   * Terapkan kedua langkah berikut:
     * Atur target crawl 4 keyword tambahan secara **seimbang** (mis. masing-masing ~`5.000`–`6.000` baris, sehingga total 5 keyword tetap nyaman di rentang Panduan **20.000–50.000+ baris**).
     * Di Spark SQL, hitung juga **kurva ternormalisasi (`volume_hari / total_volume_keyword` atau `volume_hari / volume_puncak`)** agar bentuk kenaikan dan penurunan atensi 5 topik bisa dibandingkan secara proporsional (*apple-to-apple*).

---

## 5. Rekomendasi 5 Keyword untuk Perbandingan Siklus Atensi

Agar model klasifikasi & regresi Spark MLlib memiliki variasi target durasi sorotan yang nyata (viral sesaat vs menengah vs berkelanjutan), kumpulkan kombinasi topik berikut (**jangan menekan tombol `Kosongkan!`** sebelum mengekspor dataset gabungan akhir):

| No | Rekomendasi Keyword | Kategori & Karakteristik Siklus Atensi | Sumber Kuat |
| :--- | :--- | :--- | :--- |
| 1 | `GTA 6 rilis` *(Sudah ada)* | Gaming/Teknologi — antisipasi panjang dengan lonjakan gelombang rilis/kabar berulang | YouTube, TikTok |
| 2 | `karhutla` | Bencana Ekologis — isu musiman berulang & liputan media jangka panjang | GDELT/Berita ID, IG, YouTube |
| 3 | `Pengunduran Gibran` | Politik Nasional — isu viral akut berkecepatan tinggi (*fast spike & debate*) | GDELT/Berita ID, TikTok, IG, YouTube |
| 4 | `PPN 12 persen` *(atau `harga beras`)* | Ekonomi/Kebijakan Publik — diskusi bertahap dengan pro-kontra warga berkelanjutan | GDELT/Berita ID, Facebook, YouTube |
| 5 | `Timnas Indonesia` | Olahraga — puncak periodik tajam mengikuti jadwal pertandingan lalu cepat meredup | YouTube, TikTok, IG |

> [!NOTE]
> Jika ingin cepat dan seimbang, untuk 4 keyword baru cukup set **Target / tool = `5000`**, lalu jalankan **7/7 sumber** (termasuk GDELT, Instagram, TikTok, Facebook, dan YouTube). Setelah semua selesai, ekspor ulang **`.json`** dan **`.csv`** gabungan seluruh 5 keyword dari JinwooCrawl.

---

## 6. Checklist Eksekusi Tim Selanjutnya (Sesuai Bobot Nilai Panduan UAS)

1. **[ ] Tahap 1 — Finalisasi Dataset Multi-Isu (Target Total ~25.000–45.000 baris):**
   * Lengkapi 4 keyword tambahan di JinwooCrawl, pastikan seluruh 5 keyword tersimpan bersih di MongoDB, lalu ekspor file gabungan akhir (`jinwoo_crawl_dataset.json` & `.csv`).
2. **[ ] Tahap 2 — Penyimpanan di Hadoop HDFS (`20%` bobot bersama Spark):**
   * Jalankan klaster Hadoop (Docker/WSL/STB), buat direktori `/user/bigdata/uas/raw/`, unggah dataset via `hdfs dfs -put`, dan dokumentasikan tangkapan layar (`hdfs dfs -ls` serta Web UI NameNode).
3. **[ ] Tahap 3 — Pembersihan & Transformasi di Apache Spark (`PySpark`):**
   * Baca dataset JSON dari HDFS, cek `printSchema()` dan jumlah baris, bersihkan duplikat, pisahkan `type == 'comment'` vs publikasi induk, hitung ulang sentimen teks (`content`/`title`), serta bentuk kolom fitur *Issue Attention Cycle*.
4. **[ ] Tahap 4 — Minimal 3 Analisis Spark SQL / DataFrame API:**
   * **Analisis 1:** Kurva tren volume harian & normalisasi proporsi antar 5 keyword (grafik *emergence $\rightarrow$ peak $\rightarrow$ decay*).
   * **Analisis 2:** Perhitungan *Decay Rate*, umur aktif isu, serta perbandingan engagement antar-platform (`YouTube` vs `News` vs `TikTok` vs `IG` vs `Facebook`).
   * **Analisis 3:** Identifikasi *top author/media* penyebar isu dan korelasi panjang teks / sentimen terhadap rasio komentar.
5. **[ ] Tahap 5 — Pemodelan Spark MLlib + Eksperimen Skala Data (`40%` total bobot):**
   * Bangun `Pipeline` (`Tokenizer` $\rightarrow$ `HashingTF`/`IDF` + `StringIndexer` + `VectorAssembler` + `StandardScaler`).
   * Jalankan minimal 1 model **Klasifikasi** (`RandomForestClassifier` / `LogisticRegression` $\rightarrow$ *Accuracy, Precision, Recall, F1*) dan/atau **Regresi** (`GBTRegressor` / `LinearRegression` $\rightarrow$ *RMSE, MAE*).
   * Lakukan **Eksperimen Benchmark Skala Data** (ukur waktu eksekusi pada subset `5.000` vs `15.000` vs `30.000+` baris).
   * *(Opsional nilai tambah)* Simpan ringkasan hasil prediksi Spark kembali ke **MongoDB** sesuai Panduan halaman 4 poin 6D.
6. **[ ] Tahap 6 — Penyusunan Draf Artikel Ilmiah (`15%`) & Presentasi (`15%`):**
   * Tulis artikel dalam **Bahasa Indonesia** mengikuti 7 struktur wajib di Panduan hal. 5 (`Judul`, `Abstrak`, `Pendahuluan`, `Metode Penelitian`, `Hasil & Pembahasan`, `Kesimpulan`, `Daftar Pustaka`: Anthony Downs 1972, UU PDP 27/2022, dokumentasi GDELT/API, Hadoop & Spark).
   * Cantumkan tangkapan layar arsitektur **JinwooCrawl + MongoDB + HDFS + Spark SQL + Spark MLlib** beserta pembagian kontribusi tiap anggota kelompok.
