# Analisis & Roadmap Proyek Akhir Big Data 2026: "Issue Attention Cycle"

Dokumen ini disusun sebagai panduan konseptual, metodologis, dan teknis bagi kelompok dalam mengerjakan Proyek Akhir Mata Kuliah Big Data (S1 Informatika UNESA).

---

## 1. Konteks & Ringkasan Diskusi Kelompok

* **Riset Awal (Ramzi):** Menemukan ide-ide umum seputar analisis data dan machine learning skala besar.
* **Kritik & Usulan (Shobrun):**
  * Ide awal dinilai terlalu umum (*general*).
  * Shobrun mengusulkan topik spesifik berbasis fenomena riil: **seberapa sering dan berapa lama suatu isu berita/informasi dibahas berulang kali di media dalam kurun waktu tertentu (misal 1 minggu)** (contoh isu: Karhutla, isu politik figur publik, dll).
  * Mengadopsi konsep **Issue Attention Cycle** (kurva umur topik: muncul $\rightarrow$ memuncak/viral $\rightarrow$ dibahas berulang $\rightarrow$ meredup).
  * Permasalahan yang dikaji:
    1. **Klasifikasi Durasi Sorotan:** Memprediksi apakah suatu isu masuk kategori cepat reda, menengah, atau berkelanjutan.
    2. **Prediksi Lama Hari:** Estimasi angka hari suatu topik bertahan dibahas media.
  * Algoritma Spark MLlib yang diusulkan:
    * Klasifikasi: *Naive Bayes*, *Random Forest*, atau *Logistic Regression*.
    * Regresi: *Linear Regression* atau *GBT Regressor*.

---

## 2. Evaluasi: Mengapa Ide Shobrun Sangat Tepat?

Kami **sangat setuju dan merekomendasikan** ide dari Shobrun dengan pertimbangan objektif berikut:

1. **Landasan Teori Ilmiah Kuat (*Novelty & Rigor*):**
   * Konsep *Issue Attention Cycle* dirumuskan oleh sosiolog **Anthony Downs (1972)** dalam bidang komunikasi politik dan isu publik.
   * Proyek ini tidak sekadar menjadi latihan teknis biasa (seperti klasifikasi sentimen positif/negatif yang sudah terlalu klise), melainkan riset berbasis *Computational Social Science* yang layak dipublikasikan ke jurnal/prosiding sesuai luaran mata kuliah (Draf Artikel Ilmiah).
2. **Kesesuaian dengan Panduan Proyek Akhir:**
   * **Pemilihan Dataset & Topik:** Di panduan topik no. 4 terdapat *"Klasifikasi Berita Indonesia"*. Ide Shobrun mengelevasi topik tersebut menjadi analisis siklus hidup isu secara dinamis.
   * **Rekomendasi Dosen di Panduan (Halaman 3):** Dosen secara spesifik menyebut: *"API yang dapat dipertimbangkan antara lain OpenAQ untuk data kualitas udara atau **GDELT untuk data dan metadata berita**"*. Ide ini 100% selaras dengan referensi resmi dari dosen.
   * **Syarat Analisis Spark SQL:** Sangat cocok untuk menguji 3 analisis (agregasi tren harian, laju penurunan atensi/decay rate, dan diversitas media penyebar).
   * **Syarat Spark MLlib:** Cocok untuk implementasi klasifikasi maupun regresi terdistribusi.

---

## 3. Formulasi Masalah, Unit Observasi, dan Variabel Fitur

### A. Tantangan Teknis: Definisi Unit Observasi (Data Point)
Panduan mensyaratkan dataset berjumlah **20.000 – 50.000+ baris data**. 
* Jika 1 baris dihitung sebagai 1 isu tunggal, kita akan kesulitan mengumpulkan 20.000 isu unik.
* **Solusi Terbaik (*Early-Signal Prediction*):**
  Unit observasi adalah **postingan / artikel pada 24–48 jam pertama sejak suatu isu pertama kali muncul**.
  > **Tujuan Model:** *Berdasarkan karakteristik awal (konten, sentimen, dan persebaran media di hari ke-1), dapatkah model memprediksi apakah isu tersebut akan berumur pendek (viral sesaat) atau menjadi isu berkelanjutan (sorotan panjang)?*

### B. Variabel Independen (Fitur Input untuk MLlib)

| Nama Fitur | Tipe Data | Deskripsi / Makna Bisnis |
| :--- | :--- | :--- |
| `early_volume_24h` | Integer | Jumlah postingan/berita yang terbit dalam 24 jam pertama kemunculan isu. |
| `early_engagement_rate` | Double | Rata-rata interaksi (like, share, komentar) per postingan di hari ke-1. |
| `unique_media_count` | Integer | Jumlah portal/akun berita independen yang meliput isu di fase awal. |
| `sentiment_polarity` | Double | Skor sentimen (-1 s.d. +1). Isu negatif/kontroversial cenderung hidup lebih lama. |
| `headline_length` | Integer | Panjang karakter/kata pada judul/caption berita. |
| `topic_category_idx` | Integer/Vector | Kategori topik (Politik, Bencana Alam, Kriminal, Selebriti) di-encode via `StringIndexer`. |
| `source_authority_score` | Double | Skor reputasi/pengaruh sumber media pertama yang memicu isu. |

### C. Variabel Dependen (Target) & Pemilihan Algoritma

1. **Target Klasifikasi (Durasi Sorotan):**
   * **Label Target:**
     * `0`: *Fad / Viral Sesaat* ($\le 3$ hari)
     * `1`: *Medium Attention* ($4 - 7$ hari)
     * `2`: *Enduring / Berkelanjutan* ($> 7$ hari)
   * **Algoritma Spark MLlib:** `RandomForestClassifier` (direkomendasikan karena tangguh terhadap fitur campuran) atau `LogisticRegression` (Multinomial).
   * **Evaluasi:** Accuracy, Precision, Recall, F1-Score, Confusion Matrix.
2. **Target Regresi (Estimasi Angka Hari):**
   * **Label Target:** Nilai kontinu jumlah hari isu bertahan dibahas di media (`lifespan_days`).
   * **Algoritma Spark MLlib:** `GBTRegressor` (Gradient-Boosted Trees) atau `LinearRegression`.
   * **Evaluasi:** RMSE (*Root Mean Squared Error*) dan MAE (*Mean Absolute Error*).

---

## 4. Eksplorasi Tools & API Scraping / Crawling Media Sosial Gratis (Free)

Untuk memenuhi kriteria nilai tambah dari pengumpulan data mandiri/crawling, berikut opsi *open-source* dan API gratis terbaik:

### A. TikTok (Representasi Sentimen Gen-Z & Viralisasi Instan)
1. **`omkarcloud/tiktok-scraper`** ([GitHub Repository](https://github.com/omkarcloud/tiktok-scraper))
   * **Status:** Aktif, *Open Source*, bebas biaya.
   * **Fitur:** Pencarian video via kata kunci tanpa perlu API key berbayar; output langsung JSON bersih (views, likes, komentar, created time).
2. **`davidteather/TikTok-Api`** ([GitHub Repository](https://github.com/davidteather/TikTok-Api))
   * **Status:** Library Python terpopuler untuk TikTok berbasis Playwright.
3. **`dfreelon/pyktok`** ([GitHub Repository](https://github.com/dfreelon/pyktok))
   * **Status:** Dirancang oleh akademisi untuk riset data media sosial.

### B. Instagram (Representasi Akun Media Resmi & Infografis)
1. **`Instaloader`** ([GitHub Repository](https://github.com/instaloader/instaloader))
   * **Status:** Standar emas scraping publik Instagram via Python (`pip install instaloader`).
   * **Fitur:** Mengambil postingan dari akun portal berita besar (misal `@detikcom`, `@kompascom`, `@matanajwa`) berdasarkan rentang tanggal dan tagar.
2. **`instagrapi`** ([GitHub Repository](https://github.com/subzeroid/instagrapi))
   * **Status:** Berbasis *private mobile API*, sangat cepat untuk mengekstrak postingan dan komentar.

### C. Facebook (Representasi Diskusi Publik Luas)
1. **`facebook-pages-scraper`** ([PyPI Repository](https://pypi.org/project/facebook-pages-scraper/))
   * **Status:** Ringan, mem-parse payload JSON-LD dari halaman publik media tanpa perlu browser berat.
2. **Meta Ad Library API (Resmi & Legal Meta)** ([Dokumentasi Meta](https://www.facebook.com/ads/library/api/))
   * **Status:** Akses API resmi gratis untuk melacak isu sosial, politik, dan pemilu.

### D. Solusi Cloud Automation Gratis (Anti IP Ban)
* **Apify (Free Tier \$5/Bulan - Tanpa Kartu Kredit)**:
  * Menyediakan *Actor* siap pakai: **TikTok Data Scraper**, **Instagram Scraper**, dan **Facebook Posts Scraper**.
  * Server cloud Apify mengurus proxy dan captcha. Data ribuan postingan dapat diekspor langsung ke format CSV/JSON.

### E. Sumber Tambahan yang Sangat Direkomendasikan Dosen
1. **GDELT 2.0 Doc API (`gdeltdoc`)** ([GitHub Repository](https://github.com/alex9smith/gdelt-doc-api)):
   * Tertera langsung pada Panduan UAS halaman 3.
   * Mengindeks jutaan artikel berita daring Indonesia secara *real-time* dengan metadata lengkap (tanggal, media, sentimen tone).
2. **YouTube Data API v3 (Resmi Google)**:
   * Kuota gratis 10.000 unit/hari. Sangat cocok untuk mengumpulkan video berita TV (CNN Indonesia, tvOne, KompasTV) berdasarkan tanggal tayang dan interaksi penonton.

---

## 5. Arsitektur Pipeline Sistem Sesuai Panduan UAS

```
[Sumber Data: Medsos / GDELT / Portal Berita]
                     │
                     ▼ (Scraping/API Script Python)
            [Raw Data: JSON / CSV] (Ukuran 20.000 - 50.000+ baris)
                     │
                     ▼ (hdfs dfs -put raw_dataset.csv /user/bigdata/uas/)
               [Hadoop HDFS] (Penyimpanan Terdistribusi)
                     │
                     ▼ (SparkSession.read.csv / parquet)
             [Apache Spark Data Processing]
  ├── Cleaning & Preprocessing (handling missing values, datetime parsing)
  ├── 3 Analisis Spark SQL / DataFrame API:
  │    1. Agregasi volume isu harian (tren kurva kemunculan hingga redup)
  │    2. Perhitungan Decay Rate (kecepatan penurunan atensi pasca-puncak)
  │    3. Korelasi kategori isu dengan rasio viralitas/engagement
  └── Feature Engineering (StringIndexer, VectorAssembler, StandardScaler)
                     │
                     ▼
             [Spark MLlib Pipeline]
  ├── Model 1 (Klasifikasi): RandomForestClassifier / LogisticRegression
  └── Model 2 (Regresi): GBTRegressor / LinearRegression
                     │
                     ▼
          [Eksperimen & Evaluasi Hasil]
  ├── Evaluasi Model: Accuracy, F1-Score, RMSE, MAE
  └── Eksperimen Skala Data: Benchmark waktu komputasi (10k vs 30k vs 50k baris)
                     │
                     ▼
           [Draf Artikel Ilmiah] (Template S1 Informatika UNESA)
```

---

## 6. Pertanyaan Diskusi untuk Langkah Selanjutnya

Untuk menindaklanjuti rencana di atas bersama Ramzi dan Shobrun, bagaimana keputusan kita untuk langkah berikutnya:
1. **Pemilihan Sumber Data Utama:** Apakah kita akan memfokuskan pengumpulan data pada satu platform medsos (misal **TikTok** atau **Instagram**) dikombinasikan dengan **GDELT/Portal Berita**, atau menggunakan *pre-built actor* **Apify** untuk scraping lintas platform?
2. **Pembagian Peran Kelompok:** Bagaimana pembagian tugas awal antara tim (siapa yang memegang modul *Scraping & Data Ingestion ke HDFS*, siapa yang merancang *Spark SQL Preprocessing*, dan siapa yang membangun *Pipeline Spark MLlib & Draf Artikel*)?
