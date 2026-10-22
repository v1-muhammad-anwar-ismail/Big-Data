# ANALISIS TUGAS PRAKTIKUM BIG DATA MINGGU KE-7
# TOPIK: PENGGABUNGAN PRAKTIKUM 5 (OPERASI PADA RDD) DAN PRAKTIKUM 4 (SPARK STANDALONE DI WINDOWS)

---

## 1. KESINAMBUNGAN DENGAN PRAKTIKUM SEBELUMNYA

Praktikum Minggu ke-7 merupakan puncak implementasi terpadu yang melanjutkan seluruh fondasi komputasi terdistribusi dari minggu-minggu sebelumnya:

1. **Minggu ke-3 (Tugas 1 - Pengenalan HDFS dan Docker Hadoop):**
   - Membangun klaster terdistribusi Hadoop dasar menggunakan Docker Compose.
   - Menguasai peran NameNode sebagai master metadata dan DataNode sebagai penyimpan block data fisik.
   - Menguasai perintah manipulasi berkas HDFS CLI (`mkdir`, `put`, `ls`, `cat`, `cp`).
   - Mengenal HDFS Web UI pada port 9870.

2. **Minggu ke-4 (Tugas 2 - Pemrosesan MapReduce dan Orkestrasi YARN):**
   - Menjalankan kerangka pemrosesan batch MapReduce dengan orkestrasi YARN (ResourceManager dan NodeManager).
   - Mengompilasi dan mengeksekusi program Java WordCount (`TokenizerMapper` dan `IntSumReducer`).
   - Memahami alur kerja: Map -> Shuffle and Sort -> Reduce, di mana data perantara ditulis ke disk container.
   - Memantau alokasi sumber daya pada YARN Web UI (port 8088).

3. **Minggu ke-5 (Tugas 3 - Analisis Karakteristik Penyimpanan Block HDFS):**
   - Menganalisis mekanisme pembagian berkas ke dalam block HDFS (default 128 MB dan pembagian 1 MB pada `bigfile.txt` 5 MB).
   - Memverifikasi faktor replikasi (Replication Factor = 2) dan toleransi kesalahan klaster.
   - Mengaudit penempatan block dan lokasi DataNode menggunakan perintah `hdfs fsck`.
   - Mengamati prinsip Data Locality dan memastikan data masukan tersimpan pada path HDFS: `/praktikum_Muhammad_Anwar_Ismail/hdfs/input/input.txt` dengan NameNode RPC port `8020`.

4. **Minggu ke-6 (Tugas 4 - Eksplorasi Teoretis Komputasi Apache Spark):**
   - Membahas keunggulan komputasi in-memory Apache Spark dibandingkan MapReduce berbasis disk (kecepatan hingga 100x lebih tinggi).
   - Memahami konsep fundamental Resilient Distributed Datasets (RDD): *In-memory*, *Immutable*, *Partitioned*, dan toleransi kerusakan otomatis via *Lineage Graph*.
   - Mengkaji Directed Acyclic Graph (DAG) dan prinsip *Lazy Evaluation*.
   - Menguraikan arsitektur eksekusi Spark: Driver Program, Cluster Manager (Master), Worker, Executor, dan Task.

5. **Minggu ke-7 (Tugas 5 - Implementasi Terpadu Praktikum 5 dan Praktikum 4):**
   - Mengintegrasikan dua modul praktikum resmi:
     - **Praktikum 5:** Fokus mendalam pada operasi komputasi RDD, partisi, transformasi, aksi, lazy evaluation, dan caching.
     - **Praktikum 4:** Fokus pada penyediaan infrastruktur klaster Spark Standalone (1 Master + 2 Worker) menggunakan Docker di Windows, Web UI, serta integrasi HDFS.
   - Menghubungkan engine pemrosesan Spark dengan penyimpanan HDFS dari praktikum sebelumnya.

---

## 2. SPESIFIKASI DAN DAFTAR TUGAS KEDUA MODUL PRAKTIKUM

Laporan Praktikum Minggu ke-7 mencakup dua modul panduan resmi secara eksplisit dan terpisah:

### A. Modul Praktikum 5: RDD, Transformation, Action, dan Partition pada Apache Spark
Modul ini menitikberatkan pada manipulasi data menggunakan struktur data RDD secara interaktif:
1. Membuat RDD berisi angka 1 sampai 20 dan menentukan jumlah partisinya.
2. Membuat RDD dengan 4 partisi eksplisit dan mengamati persebaran elemen menggunakan `glom()`.
3. Menggunakan transformasi `map()` untuk mengalikan setiap angka dengan 5.
4. Menggunakan transformasi `filter()` untuk menyaring bilangan genap.
5. Menggunakan transformasi `flatMap()` untuk memecah beberapa kalimat menjadi token kata.
6. Menggunakan aksi `reduce()` untuk menghitung total akumulasi nilai angka.
7. Membangun pipeline WordCount berbasis koleksi lokal (`Seq`) menggunakan `flatMap()`, `map()`, dan `reduceByKey()`.
8. Membaca berkas `input.txt` dari HDFS menggunakan fungsi `textFile()`.
9. Menjalankan pemrosesan WordCount terhadap berkas dari HDFS.
10. Menerapkan mekanisme `cache()` pada RDD dan menjalankan dua aksi berurutan untuk menguji persistensi memori.

### B. Modul Praktikum 4: Instalasi dan Menjalankan Apache Spark Standalone di Windows
Modul ini menitikberatkan pada penyediaan infrastruktur klaster dan orkestrasi internal Spark Standalone:
1. Membuat dan menjalankan klaster Spark Standalone dengan 1 Master dan 2 Worker via Docker Compose.
2. Mengambil screenshot Spark Master Web UI yang memperlihatkan 2 Worker aktif berstatus ALIVE.
3. Menjalankan lingkungan interaktif `spark-shell`.
4. Membuat RDD menggunakan method `parallelize()`.
5. Menampilkan isi RDD menggunakan action `collect()`.
6. Menentukan jumlah partisi pada RDD.
7. Menggunakan operasi `map()` dan `filter()`.
8. Membuat program WordCount dengan operasi `reduceByKey()`.
9. Membaca berkas `input.txt` dari HDFS menggunakan fungsi `textFile()`.
10. Menjalankan pemrosesan WordCount terhadap berkas dari HDFS.
11. Mengambil screenshot Spark Application UI (port 4040).

---

## 3. PEMETAAN TANGKAPAN LAYAR PADA BAB III

Sesuai permintaan restrukturisasi agar kedua praktikum terpisah secara tegas, subbab hasil dan tangkapan layar dibagi menjadi dua subbab independen:

### Subbab 3.1: Hasil dan Tangkapan Layar RDD, Transformation, Action, dan Partition pada Apache Spark (Praktikum 5)

Subbab ini memuat seluruh bukti eksekusi operasi komputasi RDD sesuai 10 butir tugas Praktikum 5:

| No. | Identitas Gambar | Deskripsi Langkah / Perintah yang Dijalankan |
|---|---|---|
| 1 | `Gambar 3.1.1 - Pembuatan RDD angka 1 sampai 20 dan pengecekan jumlah partisi default.png` | Perintah `val rdd = sc.parallelize(1 to 20)`, aksi `rdd.collect()`, dan inspeksi partisi via `rdd.getNumPartitions`. |
| 2 | `Gambar 3.1.2 - Pembuatan RDD dengan 4 partisi eksplisit dan inspeksi partisi menggunakan glom.png` | Perintah `val rdd4 = sc.parallelize(1 to 20, 4)` dan visualisasi pembagian elemen per partisi via `rdd4.glom().collect()`. |
| 3 | `Gambar 3.1.3 - Eksekusi transformasi map untuk mengalikan nilai elemen dengan 5.png` | Perintah transformasi `val rddKali = rdd.map(x => x * 5)` dan penayangan hasil via aksi `rddKali.collect()`. |
| 4 | `Gambar 3.1.4 - Eksekusi transformasi filter untuk menyaring bilangan genap.png` | Perintah transformasi `val rddGenap = rdd.filter(x => x % 2 == 0)` dan penayangan hasil via aksi `rddGenap.collect()`. |
| 5 | `Gambar 3.1.5 - Eksekusi transformasi flatMap untuk pemecahan baris kalimat menjadi kata.png` | Perintah pemecahan kalimat via `val kata = kalimat.flatMap(line => line.split(" "))` dan aksi `kata.collect()`. |
| 6 | `Gambar 3.1.6 - Eksekusi aksi count dan first pada RDD kata.png` | Perintah inspeksi cepat elemen via pemanggilan aksi `kata.count()` dan `kata.first()`. |
| 7 | `Gambar 3.1.7 - Eksekusi aksi reduce untuk menghitung nilai akumulasi total elemen.png` | Perintah kalkulasi skalar agregat total elemen numerik via `val total = rdd.reduce((a, b) => a + b)`. |
| 8 | `Gambar 3.1.8 - Pemrosesan pipeline WordCount lokal menggunakan flatMap map dan reduceByKey.png` | Pipeline WordCount berbasis `Seq(...)` via `flatMap`, `map(word => (word, 1))`, `reduceByKey((a,b) => a + b)`, dan `counts.collect()`. |
| 9 | `Gambar 3.1.9 - Pembacaan dataset HDFS ke dalam RDD menggunakan sc.textFile.png` | Pembuatan RDD dari data HDFS via `val fileHDFS = sc.textFile("hdfs://namenode:8020/...")`, `fileHDFS.count()`, dan `fileHDFS.collect()`. |
| 10 | `Gambar 3.1.10 - Eksekusi pipeline WordCount terdistribusi terhadap file HDFS.png` | Pipeline pemrosesan WordCount terdistribusi terhadap data dari HDFS hingga penayangan hasil via `countsHDFS.collect()`. |
| 11 | `Gambar 3.1.11 - Demonstrasi Lazy Evaluation pada rantai transformasi Spark.png` | Rantai transformasi `val hasilLazy = fileHDFS.filter(...).map(...)` tanpa komputasi, dipicu oleh pemanggilan aksi `hasilLazy.count()`. |
| 12 | `Gambar 3.1.12 - Pengujian mekanisme caching RDD menggunakan cache dan eksekusi dua aksi.png` | Pemanggilan `.cache()` diikuti eksekusi dua aksi `count()` berturut-turut untuk menguji pemanfaatan data dalam RAM. |
| 13 | `Gambar 3.1.13 - Antarmuka Spark Application UI pada localhost 4040 tab Jobs.png` | Tampilan browser `http://localhost:4040` tab Jobs yang mencatat riwayat eksekusi seluruh job komputasi RDD. |
| 14 | `Gambar 3.1.14 - Antarmuka Spark Application UI tab Stages dan visualisasi DAG.png` | Tampilan tab Stages dan grafik alur visual Directed Acyclic Graph (DAG) dari tahapan eksekusi RDD. |
| 15 | `Gambar 3.1.15 - Antarmuka Spark Application UI tab Executors.png` | Tampilan tab Executors yang memperlihatkan beban eksekusi task pada Driver dan Worker. |
| 16 | `Gambar 3.1.16 - Antarmuka Spark Application UI tab Storage saat RDD di-cache.png` | Tampilan tab Storage yang membuktikan RDD tersimpan dalam cache RAM (*Memory Deserialized 1x Replicated*). |

---

### Subbab 3.2: Hasil dan Tangkapan Layar Instalasi dan Menjalankan Apache Spark Standalone di Windows (Praktikum 4)

Subbab ini memuat seluruh bukti eksekusi penyiapan infrastruktur klaster sesuai 11 butir tugas Praktikum 4:

| No. | Identitas Gambar | Deskripsi Langkah / Perintah yang Dijalankan |
|---|---|---|
| 1 | `Gambar 3.2.1 - Status Docker Desktop dan versi Docker Engine serta Docker Compose.png` | Pengecekan kesiapan Docker di host Windows: output perintah `docker --version` dan `docker compose version`. |
| 2 | `Gambar 3.2.2 - Struktur direktori dan isi file konfigurasi docker-compose.spark.yml_1.png` | Verifikasi keberadaan file konfigurasi klaster di direktori kerja menggunakan perintah `dir`. |
| 3 | `Gambar 3.2.3 - Struktur direktori dan isi file konfigurasi docker-compose.spark.yml_2.png` | Penayangan isi lengkap konfigurasi service `spark-master`, `spark-worker-1`, `spark-worker-2` via `type docker-compose.spark.yml`. |
| 4 | `Gambar 3.2.4 - Status container klaster Spark Standalone menggunakan docker ps.png` | Eksekusi `docker compose -f docker-compose.spark.yml up -d` dilanjutkan `docker ps` yang membuktikan container berstatus `Up`. |
| 5 | `Gambar 3.2.5 - Antarmuka Spark Master Web UI pada localhost 8080.png` | Tampilan Web UI `http://localhost:8080` yang memperlihatkan Master URL `spark://spark-master:7077` dan dua Worker aktif berstatus ALIVE. |
| 6 | `Gambar 3.2.6 - Antarmuka Spark Worker 1 Web UI pada localhost 8081.png` | Tampilan Web UI `http://localhost:8081` yang menampilkan informasi spesifik Worker 1 (status, alokasi Core, dan alokasi RAM). |
| 7 | `Gambar 3.2.7 - Antarmuka Spark Worker 2 Web UI pada localhost 8082.png` | Tampilan Web UI `http://localhost:8082` yang menampilkan informasi spesifik Worker 2. |
| 8 | `Gambar 3.2.8 - Pengecekan versi Apache Spark di dalam container spark-master.png` | Eksekusi `docker exec -it spark-master bash` dilanjutkan `/opt/spark/bin/spark-submit --version` yang memverifikasi Spark 3.5.6. |
| 9 | `Gambar 3.2.9 - Inisialisasi dan koneksi spark-shell ke klaster Spark Standalone.png` | Eksekusi `/opt/spark/bin/spark-shell --master spark://spark-master:7077` hingga muncul prompt interaktif `scala>`. |
| 10 | `Gambar 3.2.10 - Verifikasi kesiapan file input.txt di dalam HDFS klaster Hadoop.png` | Eksekusi perintah pengecekan data HDFS di host/container: `hdfs dfs -ls /praktikum_Muhammad_Anwar_Ismail/hdfs/input`. |
| 11 | `Gambar 3.2.11 - Proses penghentian sesi spark-shell dan shutdown klaster Docker.png` | Perintah keluar sesi `:quit`, `exit`, dan shutdown klaster `docker compose down` beserta verifikasi `docker ps`. |

---

## 4. RESTRUKTURISASI DOKUMEN LAPORAN RESMI (DOCX TUGAS 5)

Berikut adalah sistematika dokumen resmi yang disesuaikan pada [161_Muhammad Anwar Ismail_TIE24_LaporanPraktikumBigData_Tugas5.docx](file:///d:/Semester%205/Big%20Data/Minggu%20ke-7/161_Muhammad%20Anwar%20Ismail_TIE24_LaporanPraktikumBigData_Tugas5.docx):

### Halaman Judul (Cover)
- Judul: **LAPORAN PRAKTIKUM SPARK DAN RDD**
- Dosen Pengampu: Ersha Aisyah Elfaiz, S.Si., M.T.I.
- Penyusun: Muhammad Anwar Ismail (24051204161)
- Program Studi S1 Teknik Informatika, Fakultas Teknik, Universitas Negeri Surabaya, 2026.

### Daftar Isi dan Daftar Gambar
- Daftar isi terstruktur memuat BAB I hingga LAMPIRAN B.
- Daftar gambar memuat Gambar 3.1.1 s.d. 3.1.16 (Praktikum 5) dan Gambar 3.2.1 s.d. 3.2.11 (Praktikum 4).

---

### BAB I: PENDAHULUAN
- **1.1 Latar Belakang:**
  Menguraikan dua pilar utama komputasi data terdistribusi modern:
  1. *Pergeseran Paradigma Infrastruktur (Praktikum 4):* Keterbatasan model MapReduce berbasis disk pada ekosistem Hadoop dalam menangani komputasi iteratif dan latensi rendah mendorong adopsi Apache Spark. Klaster Spark Standalone menghadirkan mekanisme orkestrasi terdistribusi mandiri dengan konfigurasi Master-Worker yang independen tanpa ketergantungan wajib pada manajer sumber daya eksternal seperti YARN.
  2. *Keunggulan Model Komputasi RDD (Praktikum 5):* Resilient Distributed Datasets (RDD) menjadi abstraksi data terdistribusi utama yang memungkinkan pemrosesan paralel dalam memori RAM (*in-memory*), toleransi kerusakan otomatis berbasis *Lineage Graph*, serta efisiensi eksekusi bertahap berkat prinsip *Lazy Evaluation*. Praktikum ini merupakan pembuktian empiris langsung dari konsep arsitektur yang telah dieksplorasi secara teoretis pada modul sebelumnya.
- **1.2 Tujuan Praktikum:**
  Dirumuskan secara tegas dalam dua kelompok tujuan:
  - **A. Tujuan Praktikum 5 (Operasi pada RDD):**
    1. Memahami konsep dasar Resilient Distributed Datasets (RDD) sebagai abstraksi data terdistribusi utama.
    2. Membedakan secara konseptual dan struktural antara HDFS Block pada lapisan penyimpanan (*storage layer*) dengan RDD Partition pada lapisan pemrosesan (*processing layer*).
    3. Menguasai pembuatan RDD dari koleksi data lokal (`parallelize`) dan pembacaan berkas HDFS (`textFile`).
    4. Mengimplementasikan operasi transformasi (*map*, *filter*, *flatMap*, *reduceByKey*) dan aksi (*collect*, *count*, *first*, *reduce*) pada RDD.
    5. Mengamati persebaran data pada partisi RDD menggunakan fungsi `glom()`.
    6. Membuktikan prinsip kerja *Lazy Evaluation* pada rantai transformasi Spark.
    7. Menguji efektivitas mekanisme persistensi memori (*caching*) dalam mereduksi durasi eksekusi aksi berulang.
  - **B. Tujuan Praktikum 4 (Instalasi dan Menjalankan Spark Standalone):**
    8. Mengonfigurasi dan mengoperasikan klaster Apache Spark Standalone (1 Master dan 2 Worker) menggunakan Docker di Windows.
    9. Menganalisis peran dan interaksi komponen arsitektur Spark: Spark Master, Spark Worker, Driver Program, Executor, dan Task.
    10. Mengoperasikan lingkungan interaktif `spark-shell` berbasis bahasa pemrograman Scala.
    11. Mengakses dan memantau status kesehatan klaster melalui Spark Master Web UI (port 8080) dan Worker Web UI (port 8081 dan 8082).
    12. Menganalisis visualisasi Directed Acyclic Graph (DAG), Jobs, Stages, dan Tasks melalui Spark Application UI (port 4040).
    13. Mengintegrasikan klaster Spark dengan klaster Hadoop HDFS untuk memproses dataset terdistribusi.

---

### BAB II: DASAR TEORI

Dibagi secara simetris: subbab 2.1 – 2.4 fokus pada materi Praktikum 5 (Operasi RDD), dan subbab 2.5 – 2.8 fokus pada materi Praktikum 4 (Klaster Spark Standalone):

#### Bagian A: Teori Operasi pada RDD (Fokus Praktikum 5)
- **2.1 Konsep Resilient Distributed Datasets (RDD) dan Karakteristiknya:**
  Membahas definisi RDD, 3 sifat fundamental (*In-Memory*, *Immutable*, *Partitioned*), dan mekanisme toleransi kesalahan berbasis *Lineage Graph*.
- **2.2 Komparasi HDFS Block (Lapisan Storage) vs RDD Partition (Lapisan Processing):**
  Tabel perbandingan antara unit penyimpanan fisik HDFS (Block, di DataNode, ukuran default 128 MB, replikasi) dengan unit pemrosesan logis Spark (Partition, di RAM Executor, diproses oleh Task).
- **2.3 Klasifikasi Operasi RDD: Transformations dan Actions:**
  Membahas perbedaan transformasi (menghasilkan RDD baru, bersifat lazy; *Narrow* vs *Wide Dependency*) dan aksi (memicu eksekusi dan mengembalikan hasil ke Driver).
- **2.4 Mekanisme Lazy Evaluation dan Persistensi Memori (Caching):**
  Membahas penundaan eksekusi oleh engine Spark hingga aksi dipanggil, serta fungsi optimasi `cache()` / `persist()` untuk menghindari komputasi ulang (*recomputation*).

#### Bagian B: Teori Klaster Spark Standalone (Fokus Praktikum 4)
- **2.5 Arsitektur Klaster Apache Spark Standalone:**
  Membahas peran Master Node (RPC 7077, Web UI 8080), Worker Nodes (Web UI 8081/8082), Driver Program, Executor, dan Task.
- **2.6 Lingkungan Interaktif Spark Shell dan Ekosistem Scala:**
  Membahas fungsi `spark-shell` sebagai REPL interaktif, inisialisasi otomatis `sc` (*SparkContext*) dan `spark` (*SparkSession*), serta sintaks ekspresif Scala.
- **2.7 Pengawasan Klaster dan Aplikasi melalui Spark Web UI:**
  Membahas perbedaan pengawasan makro klaster pada Spark Master UI (port 8080) dan pengawasan mikro aplikasi pada Spark Application UI (port 4040).
- **2.8 Komparasi Model Deployment: Spark Standalone vs Spark on YARN:**
  Tabel perbandingan alur eksekusi: Standalone (Driver -> Master -> Worker -> Executor) vs YARN (Driver -> ResourceManager -> NodeManager/Container -> Executor).

---

### BAB III: PEMBAHASAN

Struktur BAB III menjadi sangat sistematis dan proporsional:
- **3.1 Hasil dan Tangkapan Layar RDD, Transformation, Action, dan Partition pada Apache Spark:**
  Menyajikan Gambar 3.1.1 sampai 3.1.16 beserta potongan kode dan ulasan analisis teknis (fokus Praktikum 5).
- **3.2 Hasil dan Tangkapan Layar Instalasi dan Menjalankan Apache Spark Standalone di Windows:**
  Menyajikan Gambar 3.2.1 sampai 3.2.11 beserta potongan kode dan ulasan analisis teknis (fokus Praktikum 4).
- **3.3 Analisis dan Pembahasan Operasi pada RDD (Praktikum 5):**
  - Analisis mekanisme pemartisian data dan verifikasi distribusi data per partisi menggunakan `glom()`.
  - Analisis perbedaan karakteristik pemetaan: transformasi 1-to-1 pada `map()` vs transformasi 1-to-N dan flattening pada `flatMap()`.
  - Analisis perbedaan fungsi agregasi: `reduce()` (agregasi skalar seluruh dataset) vs `reduceByKey()` (agregasi key-value dengan map-side combine).
  - Pembuktian empiris *Lazy Evaluation* dan analisis peningkatan performa berkat fungsi `cache()`.
- **3.4 Analisis dan Pembahasan Klaster Spark Standalone dan Integrasi HDFS (Praktikum 4):**
  - Analisis arsitektur Spark Standalone: alur registrasi Worker ke Master, alokasi Core dan RAM pada Worker 1 dan 2, serta alur peluncuran Executor dari Driver.
  - Analisis komparasi operasional: kelebihan kesederhanaan manajemen sumber daya Spark Standalone dibandingkan overhead negosiasi container pada YARN (Tugas 2 & 3).
  - Analisis mekanisme integrasi HDFS Storage Layer dengan Spark Processing Layer: pembacaan berkas `input.txt` dari NameNode (`hdfs://namenode:8020`), peran Docker network bridging, dan keunggulan kecepatan WordCount Spark in-memory dibanding MapReduce disk-based.

---

### BAB IV: KESIMPULAN
- **4.1 Kesimpulan:**
  Sintesis menyeluruh yang merangkum keberhasilan implementasi klaster Spark Standalone (Praktikum 4) dan keunggulan komputasi data terdistribusi menggunakan operasi RDD (Praktikum 5).

---

### LAMPIRAN A: COMMAND UTAMA
Tabel komprehensif berisi 20 perintah utama Docker, Bash container, dan Spark Shell Scala yang digunakan pada praktikum.

### LAMPIRAN B: PORT YANG DIGUNAKAN
Tabel pemetaan seluruh port layanan Spark (8080, 7077, 8081, 8082, 4040) dan Hadoop (9870, 8020, 8088).
