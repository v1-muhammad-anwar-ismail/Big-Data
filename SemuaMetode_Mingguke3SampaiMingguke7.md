# PANDUAN LENGKAP METODE PRAKTIKUM BIG DATA (MINGGU 3 SAMPAI MINGGU 7)
## Buku Panduan Praktikum, Ujian Tengah Semester (UTS), dan Eksplorasi Sistem Terdistribusi
### Berbasis Klaster Terpadu: Apache Hadoop 3.4.3 (HDFS & YARN) dan Apache Spark 3.5.6 (Standalone)
**Penyusun:** Muhammad Anwar Ismail (NIM: 24051204161)  
**Program Studi:** S1 Teknik Informatika, Fakultas Teknik, Universitas Negeri Surabaya  
**File Konfigurasi Utama:** [docker-compose.yml](file:///d:/Semester%205/Big%20Data/Minggu%20ke-7/spark-praktikum/docker-compose.yml)

---

## DAFTAR ISI

1. [Arsitektur Klaster Terpadu (Unified Docker Compose)](#1-arsitektur-klaster-terpadu-unified-docker-compose)
2. [Manajemen Dataset (Kecil, Besar, dan Input Manual)](#2-manajemen-dataset-kecil-besar-dan-input-manual)
3. [Minggu ke-3: Fondasi HDFS dan Manipulasi Berkas Terdistribusi](#3-minggu-ke-3-fondasi-hdfs-dan-manipulasi-berkas-terdistribusi)
4. [Minggu ke-4: Komputasi MapReduce Java dan Orkestrasi YARN](#4-minggu-ke-4-komputasi-mapreduce-java-dan-orkestrasi-yarn)
5. [Minggu ke-5: Karakteristik Block HDFS, Replikasi, dan Data Locality](#5-minggu-ke-5-karakteristik-block-hdfs-replikasi-dan-data-locality)
6. [Minggu ke-6: Landasan Teori Komparasi MapReduce vs Apache Spark](#6-minggu-ke-6-landasan-teori-komparasi-mapreduce-vs-apache-spark)
7. [Minggu ke-7: Apache Spark Standalone dan Operasi Komprehensif RDD](#7-minggu-ke-7-apache-spark-standalone-dan-operasi-komprehensif-rdd)
8. [Matriks Perintah Cepat (Cheat Sheet CLI)](#8-matriks-perintah-cepat-cheat-sheet-cli)
9. [Panduan Pemecahan Masalah (Troubleshooting Saat Ujian Praktikum)](#9-panduan-pemecahan-masalah-troubleshooting-saat-ujian-praktikum)
10. [Variasi Skenario Soal Ujian dan Pola Solusi](#10-variasi-skenario-soal-ujian-dan-pola-solusi)

---

## 1. ARSITEKTUR KLASTER TERPADU (UNIFIED DOCKER COMPOSE)

Seluruh praktikum dari Minggu ke-3 hingga Minggu ke-7 dapat dijalankan menggunakan satu file konfigurasi terpadu: `docker-compose.yml` yang berada di folder `Minggu ke-7\spark-praktikum`.

### 1.1 Struktur 9 Kontainer dan Fungsinya

| No | Nama Kontainer | Layanan / Peran | Port Host / Port Kontainer | Fungsi Utama |
|---|---|---|---|---|
| 1 | `namenode` | HDFS Master | `9870:9870`, `8020:8020` | Pengelola metadata direktori berkas dan koordinator block HDFS |
| 2 | `datanode1` | HDFS Worker 1 | Internal (9864) | Penyimpan fisik block data HDFS primer |
| 3 | `datanode2` | HDFS Worker 2 | Internal (9864) | Penyimpan fisik block data HDFS sekunder (memungkinkan Replication Factor = 2) |
| 4 | `resourcemanager` | YARN Master | `8088:8088` | Pengelola sumber daya klaster dan penjadwal antrean job MapReduce |
| 5 | `nodemanager1` | YARN Worker 1 | `8042:8042` | Eksekutor container MapReduce pada node 1 |
| 6 | `nodemanager2` | YARN Worker 2 | `8043:8042` | Eksekutor container MapReduce pada node 2 |
| 7 | `spark-master` | Spark Master | `7077:7077`, `8080:8080`, `4040:4040` | Koordinator klaster Spark Standalone dan host Driver Program |
| 8 | `spark-worker-1` | Spark Worker 1 | `8081:8081` | Penyedia alokasi CPU core dan RAM untuk eksekusi Task Spark |
| 9 | `spark-worker-2` | Spark Worker 2 | `8082:8081` | Penyedia alokasi CPU core dan RAM kedua untuk eksekusi paralel |

### 1.2 Syarat Mutlak Direktori Konfigurasi (`conf/`)
Kontainer Hadoop membutuhkan empat file XML konfigurasi yang wajib berada di folder `./conf` sejajar dengan file `docker-compose.yml`:
- `core-site.xml` -> Mendefinisikan URI RPC NameNode: `hdfs://namenode:8020`.
- `hdfs-site.xml` -> Mendefinisikan replikasi default (1) dan path penyimpanan internal.
- `mapred-site.xml` -> Mendefinisikan framework YARN dan environment `HADOOP_MAPRED_HOME=/opt/hadoop`.
- `yarn-site.xml` -> Mendefinisikan hostname resource manager dan shuffle service.

### 1.3 Perintah Operasi Klaster Terpadu
Jalankan perintah ini di Command Prompt Windows pada direktori `D:\Semester 5\Big Data\Minggu ke-7\spark-praktikum`:

```cmd
:: Menyalakan seluruh 9 kontainer klaster
docker compose up -d

:: Memeriksa status kesehatan kontainer (seluruhnya harus berstatus 'Up')
docker ps

:: Mematikan seluruh klaster dan membersihkan alokasi memori
docker compose down
```

---

## 2. MANAJEMEN DATASET (KECIL, BESAR, DAN INPUT MANUAL)

Dalam praktikum atau ujian, dosen dapat memberikan data dengan tiga metode berbeda. Berikut adalah cara penanganan masing-masing skenario dari host Windows hingga masuk ke HDFS:

### Skenario A: Input Data Manual (Membuat Berkas Langsung)

#### Cara 1: Dibuat di Host Windows lalu Disalin ke Kontainer
1. Buat berkas teks menggunakan Notepad atau CMD:
   ```cmd
   echo Big Data Terdistribusi Teknik Informatika UNESA Surabaya > data_manual.txt
   echo Apache Hadoop dan Apache Spark untuk Pengolahan Skala Besar >> data_manual.txt
   ```
2. Salin berkas dari Windows ke dalam kontainer NameNode:
   ```cmd
   docker cp data_manual.txt namenode:/tmp/data_manual.txt
   ```
3. Masuk ke NameNode dan unggah ke direktori HDFS:
   ```cmd
   docker exec -it --user hadoop namenode bash
   hdfs dfs -mkdir -p /praktikum_Muhammad_Anwar_Ismail/hdfs/input
   hdfs dfs -put -f /tmp/data_manual.txt /praktikum_Muhammad_Anwar_Ismail/hdfs/input/data_manual.txt
   hdfs dfs -cat /praktikum_Muhammad_Anwar_Ismail/hdfs/input/data_manual.txt
   exit
   ```

#### Cara 2: Dibuat Langsung di Dalam Kontainer Linux
```cmd
docker exec -it --user hadoop namenode bash
cat << 'EOF' > /tmp/input_langsung.txt
Hadoop HDFS menyimpan data terdistribusi
Spark memproses data di dalam memori
MapReduce memproses data berbasis disk
EOF
hdfs dfs -put -f /tmp/input_langsung.txt /praktikum_Muhammad_Anwar_Ismail/hdfs/input/input_langsung.txt
exit
```

---

### Skenario B: Dataset Kecil (Berkas CSV / TXT Eksternal dari Dosen)
Jika dosen memberikan berkas dataset misalnya `dataset_kecil.csv` atau `input.txt`:
1. Letakkan berkas tersebut di folder kerja Windows Anda (misal `D:\Semester 5\Big Data\dataset_kecil.csv`).
2. Salin berkas ke kontainer NameNode:
   ```cmd
   docker cp "D:\Semester 5\Big Data\dataset_kecil.csv" namenode:/tmp/dataset_kecil.csv
   ```
3. Unggah ke HDFS dan verifikasi ukurannya:
   ```cmd
   docker exec -it --user hadoop namenode hdfs dfs -put -f /tmp/dataset_kecil.csv /praktikum_Muhammad_Anwar_Ismail/hdfs/input/
   docker exec -it --user hadoop namenode hdfs dfs -ls -h /praktikum_Muhammad_Anwar_Ismail/hdfs/input/dataset_kecil.csv
   ```

---

### Skenario C: Dataset Besar (Skala Megabyte / Banyak Baris untuk Menguji Partisi dan Block)
Jika dosen meminta dataset berukuran besar untuk membuktikan pemecahan block HDFS atau partisi Spark:

#### 1. Membuat Berkas Besar di Windows (Looping Baris Teks)
Jalankan perintah looping di Command Prompt Windows:
```cmd
:: Membuat berkas 125.000 baris (ukuran sekitar 5,1 MB)
for /L %i in (1,1,125000) do @echo Hadoop HDFS DataNode MapReduce Big Data>>bigfile.txt
```
Periksa ukuran berkas:
```cmd
dir bigfile.txt
```

#### 2. Menyalin ke Kontainer NameNode
```cmd
docker cp bigfile.txt namenode:/tmp/bigfile.txt
```

#### 3. Mengunggah ke HDFS dengan Parameter Block Size Kustom
Default block size HDFS adalah 128 MB (134.217.728 byte). Agar berkas 5 MB dapat terpecah menjadi beberapa block di DataNode, gunakan opsi `-Ddfs.blocksize=1048576` (1 MB per block) dan `-Ddfs.replication=2`:
```cmd
docker exec -it --user hadoop namenode bash
hdfs dfs -mkdir -p /praktikum_Muhammad_Anwar_Ismail/hdfs/biginput
hdfs dfs -Ddfs.blocksize=1048576 -Ddfs.replication=2 -put -f /tmp/bigfile.txt /praktikum_Muhammad_Anwar_Ismail/hdfs/biginput/bigfile.txt
hdfs dfs -ls /praktikum_Muhammad_Anwar_Ismail/hdfs/biginput/
exit
```

#### 4. Audit Penempatan Block Menggunakan `hdfs fsck`
Perintah ini membuktikan pemecahan berkas besar ke DataNode:
```cmd
docker exec -it --user hadoop namenode /opt/hadoop/bin/hdfs fsck /praktikum_Muhammad_Anwar_Ismail/hdfs/biginput/bigfile.txt -files -blocks -locations
```
*Hasil:* Berkas 5 MB terpecah menjadi 5 block (`blk_...`), dengan masing-masing block memiliki 2 salinan (*replica*) yang tersebar di `datanode1` dan `datanode2`.

---

## 3. MINGGU KE-3: FONDASI HDFS DAN MANIPULASI BERKAS TERDISTRIBUSI

Fokus: Memahami arsitektur NameNode (metadata) dan DataNode (data fisik), CLI HDFS, serta Web UI.

### 3.1 Pengecekan Kesehatan Klaster HDFS
Jalankan laporan status DataNode dari CMD Windows:
```cmd
docker exec -it --user hadoop namenode /opt/hadoop/bin/hdfs dfsadmin -report
```
*Poin Pengamatan:*
- `Live datanodes`: Harus bernilai 2 (`datanode1` dan `datanode2`).
- `Configured Capacity`: Menampilkan total kapasitas penyimpanan klaster.
- Status node harus `Normal`.

### 3.2 Katalog Perintah Lengkap HDFS CLI
Seluruh perintah dijalankan melalui `docker exec -it --user hadoop namenode /opt/hadoop/bin/hdfs dfs [perintah]`:

1. **Membuat Direktori Bersarang (`-mkdir -p`):**
   ```cmd
   docker exec -it --user hadoop namenode /opt/hadoop/bin/hdfs dfs -mkdir -p /praktikum_Muhammad_Anwar_Ismail/hdfs/input
   ```
2. **Mengunggah Berkas dari Lokal Kontainer ke HDFS (`-put`):**
   ```cmd
   docker exec -it --user hadoop namenode /opt/hadoop/bin/hdfs dfs -put -f /tmp/input.txt /praktikum_Muhammad_Anwar_Ismail/hdfs/input/
   ```
3. **Melihat Isi Direktori HDFS (`-ls` atau `-ls -R`):**
   ```cmd
   docker exec -it --user hadoop namenode /opt/hadoop/bin/hdfs dfs -ls /praktikum_Muhammad_Anwar_Ismail/hdfs/input
   ```
4. **Membaca Konten Berkas di HDFS (`-cat`):**
   ```cmd
   docker exec -it --user hadoop namenode /opt/hadoop/bin/hdfs dfs -cat /praktikum_Muhammad_Anwar_Ismail/hdfs/input/input.txt
   ```
5. **Menyalin Berkas di Dalam HDFS (`-cp`):**
   ```cmd
   docker exec -it --user hadoop namenode /opt/hadoop/bin/hdfs dfs -cp /praktikum_Muhammad_Anwar_Ismail/hdfs/input/input.txt /praktikum_Muhammad_Anwar_Ismail/hdfs/salinan.txt
   ```
6. **Memindahkan atau Mengubah Nama Berkas (`-mv`):**
   ```cmd
   docker exec -it --user hadoop namenode /opt/hadoop/bin/hdfs dfs -mv /praktikum_Muhammad_Anwar_Ismail/hdfs/salinan.txt /praktikum_Muhammad_Anwar_Ismail/hdfs/input/salinan_baru.txt
   ```
7. **Mengunduh Berkas dari HDFS ke Lokal Kontainer (`-get`):**
   ```cmd
   docker exec -it --user hadoop namenode /opt/hadoop/bin/hdfs dfs -get /praktikum_Muhammad_Anwar_Ismail/hdfs/input/input.txt /tmp/hasil_unduh.txt
   ```
8. **Menghapus Berkas atau Folder Rekursif (`-rm -r`):**
   ```cmd
   docker exec -it --user hadoop namenode /opt/hadoop/bin/hdfs dfs -rm -r /praktikum_Muhammad_Anwar_Ismail/hdfs/output
   ```

### 3.3 Akses Web UI HDFS
Buka browser: `http://localhost:9870`
- Menu **Overview**: Informasi klaster, kapasitas, dan status NameNode.
- Menu **Datanodes**: Daftar DataNode yang aktif beserta volume penyimpanannya.
- Menu **Utilities -> Browse the file system**: Eksplorasi hierarki direktori HDFS secara grafis.

---

## 4. MINGGU KE-4: KOMPUTASI MAPREDUCE JAVA DAN ORKESTRASI YARN

Fokus: Membangun, mengompilasi, memaketkan, dan menjalankan kode Java MapReduce menggunakan ResourceManager dan NodeManager.

### 4.1 Struktur Lengkap Kode Java WordCount (`WordCount.java`)

Simpan kode berikut sebagai `WordCount.java` di Windows:

```java
import java.io.IOException;
import java.util.StringTokenizer;
import org.apache.hadoop.conf.Configuration;
import org.apache.hadoop.fs.Path;
import org.apache.hadoop.io.IntWritable;
import org.apache.hadoop.io.Text;
import org.apache.hadoop.mapreduce.Job;
import org.apache.hadoop.mapreduce.Mapper;
import org.apache.hadoop.mapreduce.Reducer;
import org.apache.hadoop.mapreduce.lib.input.FileInputFormat;
import org.apache.hadoop.mapreduce.lib.output.FileOutputFormat;

public class WordCount {

  // KELAS MAPPER: Menerima baris teks, memecahnya menjadi kata, dan menghasilkan tuple (kata, 1)
  public static class TokenizerMapper
       extends Mapper<Object, Text, Text, IntWritable> {

    private final static IntWritable one = new IntWritable(1);
    private Text word = new Text();

    public void map(Object key, Text value, Context context)
        throws IOException, InterruptedException {
      // StringTokenizer memecah string berdasarkan spasi
      StringTokenizer itr = new StringTokenizer(value.toString());
      while (itr.hasMoreTokens()) {
        word.set(itr.nextToken().toLowerCase().replaceAll("[^a-zA-Z0-9]", "")); // Pembersihan tanda baca
        if (!word.toString().isEmpty()) {
          context.write(word, one);
        }
      }
    }
  }

  // KELAS REDUCER: Menerima pasangan key dan daftar value: (kata, [1, 1, 1, ...]) lalu menjumlahkannya
  public static class IntSumReducer
       extends Reducer<Text, IntWritable, Text, IntWritable> {

    private IntWritable result = new IntWritable();

    public void reduce(Text key, Iterable<IntWritable> values, Context context)
        throws IOException, InterruptedException {
      int sum = 0;
      for (IntWritable val : values) {
        sum += val.get();
      }
      result.set(sum);
      context.write(key, result); // Menghasilkan tuple akhir (kata, jumlah)
    }
  }

  // METODE UTAMA (DRIVER PROGRAM): Mengonfigurasi dan mengeksekusi job MapReduce ke YARN
  public static void main(String[] args) throws Exception {
    Configuration conf = new Configuration();
    Job job = Job.getInstance(conf, "Word Count Praktikum");
    
    job.setJarByClass(WordCount.class);
    job.setMapperClass(TokenizerMapper.class);
    job.setCombinerClass(IntSumReducer.class); // Opsional: Combiner untuk efisiensi lokal
    job.setReducerClass(IntSumReducer.class);
    
    job.setOutputKeyClass(Text.class);
    job.setOutputValueClass(IntWritable.class);
    
    // args[0] = Path Input HDFS; args[1] = Path Output HDFS
    FileInputFormat.addInputPath(job, new Path(args[0]));
    FileOutputFormat.setOutputPath(job, new Path(args[1]));
    
    System.exit(job.waitForCompletion(true) ? 0 : 1);
  }
}
```

---

### 4.2 Langkah Rinci Kompilasi dan Eksekusi di YARN (Langkah Demi Langkah)

Jalankan perintah ini secara berurutan:

#### 1. Salin File Java ke Kontainer NameNode
```cmd
docker cp WordCount.java namenode:/tmp/WordCount.java
```

#### 2. Masuk ke Kontainer NameNode
```cmd
docker exec -it --user hadoop namenode bash
```

#### 3. Buat Folder Build dan Kompilasi Berkas Java
Gunakan classpath Hadoop bawaan agar seluruh library MapReduce ter-load:
```bash
cd /tmp
mkdir -p classes
javac -classpath "$(/opt/hadoop/bin/hadoop classpath)" -d classes WordCount.java
```
*Catatan:* Jika tidak ada pesan error, file `.class` berhasil dibuat di dalam folder `classes/`.

#### 4. Buat Arsip Berkas JAR
```bash
jar -cvf wordcount.jar -C classes/ .
```
Periksa isi jar:
```bash
ls -lh wordcount.jar
```

#### 5. Pastikan Folder Output HDFS Belum Ada (ATURAN MUTLAK HADOOP)
Hadoop akan melempar error `FileAlreadyExistsException` jika folder output sudah ada. Hapus terlebih dahulu jika pernah dieksekusi sebelumnya:
```bash
/opt/hadoop/bin/hdfs dfs -rm -r /praktikum_Muhammad_Anwar_Ismail/hdfs/output
```

#### 6. Eksekusi Job MapReduce Menggunakan YARN
```bash
/opt/hadoop/bin/yarn jar /tmp/wordcount.jar WordCount /praktikum_Muhammad_Anwar_Ismail/hdfs/input /praktikum_Muhammad_Anwar_Ismail/hdfs/output
```
*Poin Pengamatan Terminal:*
- YARN akan menampilkan `Application ID` (contoh: `application_1790..._0001`).
- Progress `map 0% reduce 0%` -> `map 100% reduce 0%` -> `map 100% reduce 100%`.
- Status akhir: `Job ... completed successfully`.

#### 7. Memeriksa dan Menampilkan Hasil Akhir di HDFS
```bash
/opt/hadoop/bin/hdfs dfs -ls /praktikum_Muhammad_Anwar_Ismail/hdfs/output
/opt/hadoop/bin/hdfs dfs -cat /praktikum_Muhammad_Anwar_Ismail/hdfs/output/part-r-00000
exit
```
Direktori output akan memuat berkas `_SUCCESS` (penanda sukses) dan `part-r-00000` (berisi daftar kata dan frekuensinya).

### 4.3 Akses Web UI YARN
Buka browser: `http://localhost:8088`
- Tabel **Applications**: Memperlihatkan job MapReduce, status `FINISHED`, final status `SUCCEEDED`, durasi waktu, serta user `hadoop`.
- Menu **Nodes**: Memperlihatkan dua NodeManager aktif (`nodemanager1` dan `nodemanager2`).

---

## 5. MINGGU KE-5: KARAKTERISTIK BLOCK HDFS, REPLIKASI, DAN DATA LOCALITY

Fokus: Membedah mekanisme pembagian fisik block HDFS, audit dengan fsck, dan prinsip Data Locality.

### 5.1 Perintah Pengecekan Parameter Default Klaster
```cmd
:: Cek default replication factor (biasanya bernilai 1 atau diset manual 2)
docker exec -it --user hadoop namenode /opt/hadoop/bin/hdfs getconf -confKey dfs.replication

:: Cek default block size (134217728 bytes = 128 MB)
docker exec -it --user hadoop namenode /opt/hadoop/bin/hdfs getconf -confKey dfs.blocksize
```

### 5.2 Pengujian File Berukuran Kecil vs File Berukuran Besar
1. **File Kecil (`input.txt` ~132 byte):**
   Hanya membentuk **1 Block** di HDFS karena ukurannya jauh lebih kecil dari blocksize.
   Cek dengan fsck:
   ```cmd
   docker exec -it --user hadoop namenode /opt/hadoop/bin/hdfs fsck /praktikum_Muhammad_Anwar_Ismail/hdfs/input/input.txt -files -blocks -locations
   ```
2. **File Besar (`bigfile.txt` ~5 MB dengan blocksize 1 MB):**
   Membentuk **5 Block** berbeda (`blk_...`). Setiap block memiliki 2 salinan yang tersebar di `datanode1` dan `datanode2`.
   Cek dengan fsck:
   ```cmd
   docker exec -it --user hadoop namenode /opt/hadoop/bin/hdfs fsck /praktikum_Muhammad_Anwar_Ismail/hdfs/biginput/bigfile.txt -files -blocks -locations
   ```

### 5.3 Menjalankan MapReduce pada File Multi-Block dan Analisis Data Locality
Jalankan job WordCount terhadap berkas `bigfile.txt`:
```bash
docker exec -it --user hadoop namenode bash
/opt/hadoop/bin/hdfs dfs -rm -r /praktikum_Muhammad_Anwar_Ismail/hdfs/bigoutput
/opt/hadoop/bin/yarn jar /tmp/wordcount.jar WordCount /praktikum_Muhammad_Anwar_Ismail/hdfs/biginput /praktikum_Muhammad_Anwar_Ismail/hdfs/bigoutput
exit
```
*Analisis Job Counter:*
- `Launched map tasks = 5`: Jumlah Mapper persis sama dengan jumlah block HDFS (5 block = 5 Mapper).
- `Rack-local map tasks = 5`: Membuktikan prinsip **Data Locality**, di mana tugas Mapper dieksekusi sedekat mungkin dengan DataNode penyimpan block data.
- **Mengapa data tidak dihitung dua kali meskipun ada 2 replica?**
  Karena scheduler hanya menugaskan 1 Mapper untuk membaca salah satu replica yang aktif. Replica kedua hanya berfungsi sebagai cadangan (*fault tolerance*) apabila DataNode pertama padam.

---

## 6. MINGGU KE-6: LANDASAN TEORI KOMPARASI MAPREDUCE VS APACHE SPARK

Sebagai persiapan ujian lisan / esai tertulis pada UTS:

| Dimensi Perbandingan | Hadoop MapReduce | Apache Spark |
|---|---|---|
| **Penyimpanan Antartahap** | Menulis data perantara (*intermediate data*) ke hard disk | Mempertahankan data perantara di memori RAM (*In-Memory*) |
| **Kecepatan Komputasi** | Relatif lambat (terkendala I/O disk) | Hingga 100x lebih cepat untuk komputasi iteratif |
| **Model Eksekusi** | Batch terstruktur kaku (Map -> Shuffle -> Reduce) | Fleksibel berbasis Directed Acyclic Graph (DAG) |
| **Evaluasi Kode** | Eager execution (setiap tahap langsung diproses) | *Lazy Evaluation* (eksekusi ditunda sampai ada aksi) |
| **Toleransi Kerusakan** | Replikasi block data fisik pada disk DataNode | Rekonstruksi logis partisi hilang via *Lineage Graph* |

### Empat Sifat Utama RDD (*Resilient Distributed Datasets*):
1. **In-Memory:** Data dimuat dan diproses di RAM para Executor.
2. **Immutable:** RDD tidak dapat diubah setelah dibuat; transformasi menghasilkan RDD baru.
3. **Partitioned:** Dataset dipecah ke dalam partisi-partisi logis yang dikerjakan secara paralel.
4. **Fault-Tolerant:** Jika partisi rusak, Spark menghitung ulang partisi tersebut menggunakan rantai riwayat *Lineage Graph*.

---

## 7. MINGGU KE-7: APACHE SPARK STANDALONE DAN OPERASI KOMPREHENSIF RDD

Fokus: Mengoperasikan shell interaktif `spark-shell` (Scala), pemartisian RDD, transformasi, aksi, pembuktian lazy evaluation, caching, serta integrasi pembacaan HDFS.

### 7.1 Memulai Sesi Spark Shell
Dari Command Prompt Windows, masuk ke master Spark:
```cmd
docker exec -it spark-master bash
```
Jalankan spark-shell yang terhubung ke klaster Standalone:
```bash
/opt/spark/bin/spark-shell --master spark://spark-master:7077
```
Tunggu hingga muncul prompt interaktif `scala>`.

---

### 7.2 Koleksi Lengkap Kode Scala RDD

Ketikkan kode berikut langsung di prompt `scala>`:

#### 1. Pembuatan RDD Numerik dan Pengecekan Partisi Default
```scala
val rdd = sc.parallelize(1 to 20)
rdd.collect()            // Menampilkan isi: Array(1, 2, ..., 20)
rdd.getNumPartitions     // Menampilkan jumlah partisi default
```

#### 2. Menentukan Partisi Eksplisit dan Inspeksi Distribusi Data via `glom()`
Fungsi `glom()` mengelompokkan elemen ke dalam array berdasarkan partisi tempat ia berada:
```scala
val rdd4 = sc.parallelize(1 to 20, 4)
rdd4.getNumPartitions    // Menampilkan: 4
rdd4.glom().collect()    // Menampilkan pembagian: Array(Array(1..5), Array(6..10), Array(11..15), Array(16..20))
```

#### 3. Transformasi: `map()` (Perkalian Elemen)
Transformasi 1-ke-1 yang memetakan setiap elemen ke nilai baru:
```scala
val rddKali = rdd.map(x => x * 5)
rddKali.collect()        // Hasil: Array(5, 10, 15, ..., 100)
```

#### 4. Transformasi: `filter()` (Penyaringan Nilai Genap)
Menyaring data berdasarkan kondisi boolean:
```scala
val rddGenap = rdd.filter(x => x % 2 == 0)
rddGenap.collect()       // Hasil: Array(2, 4, 6, 8, 10, 12, 14, 16, 18, 20)
```

#### 5. Transformasi: `flatMap()` vs `map()` (Pemecah Kalimat Menjadi Kata)
`flatMap` memecah 1 elemen menjadi banyak elemen lalu meratakannya menjadi satu RDD datar:
```scala
val kalimat = sc.parallelize(Seq("Hadoop Spark", "Big Data Terdistribusi UNESA"))
val kata = kalimat.flatMap(line => line.split(" "))
kata.collect()           // Hasil: Array(Hadoop, Spark, Big, Data, Terdistribusi, UNESA)
```

#### 6. Aksi: `count()`, `first()`, dan `reduce()`
Aksi mengambil hasil komputasi kembali ke Driver:
```scala
kata.count()             // Menghitung total kata (Aksi)
kata.first()             // Mengambil elemen pertama: "Hadoop" (Aksi)

val total = rdd.reduce((a, b) => a + b) // Agregasi seluruh angka 1 s.d 20: 210
```

#### 7. Pipeline WordCount Lokal Menggunakan `reduceByKey()`
Agregasi pasangan kunci-nilai (*key-value pair*):
```scala
val teks = sc.parallelize(Seq("spark hadoop", "spark big data", "hadoop data"))
val words = teks.flatMap(line => line.split(" "))
val pairs = words.map(word => (word, 1))
val counts = pairs.reduceByKey((a, b) => a + b)
counts.collect()         // Hasil: Array((spark,2), (hadoop,2), (data,2), (big,1))
```

#### 8. Pembacaan Dataset dari Hadoop HDFS Menggunakan `textFile()`
Spark membaca berkas `input.txt` yang tersimpan di HDFS:
```scala
val fileHDFS = sc.textFile("hdfs://namenode:8020/praktikum_Muhammad_Anwar_Ismail/hdfs/input/input.txt")
fileHDFS.count()         // Menghitung baris
fileHDFS.collect()       // Menampilkan baris
```

#### 9. WordCount Terdistribusi Skala Penuh dari Sumber HDFS
```scala
val wordsHDFS = fileHDFS.flatMap(line => line.split("\\s+"))
val pairsHDFS = wordsHDFS.map(word => (word, 1))
val countsHDFS = pairsHDFS.reduceByKey((a, b) => a + b)
countsHDFS.collect()
```

#### 10. Pembuktian Empiris Prinsip *Lazy Evaluation*
```scala
// Baris ini TIDAK menjalankan komputasi apa pun di klaster (hanya merancang DAG):
val hasilLazy = fileHDFS.filter(line => line.nonEmpty).map(line => line.toUpperCase)

// Barulah saat aksi count() dipanggil, Spark benar-benar mengeksekusi job:
hasilLazy.count()
```

#### 11. Pengujian Mekanisme Caching Memori (`cache()`)
```scala
val dataCache = fileHDFS.filter(line => line.nonEmpty).cache()

// Eksekusi aksi pertama: Membaca HDFS, memproses, dan menyimpan hasil ke RAM
dataCache.count()

// Eksekusi aksi kedua: Langsung membaca dari RAM (durasi jauh lebih cepat!)
dataCache.count()
```

---

### 7.3 Pengawasan Antarmuka Web Spark
**PENTING: Jangan keluar dari `scala>` sebelum memeriksa Web UI!**

1. **Spark Master UI (`http://localhost:8080`):**
   - Menampilkan status klaster: *Alive Workers: 2*.
   - Tabel *Running Applications*: Menampilkan sesi `Spark shell` yang aktif dengan alokasi core dan memory.
2. **Spark Application UI (`http://localhost:4040`):**
   - Tab **Jobs**: Menampilkan daftar seluruh job yang pernah dieksekusi (`count`, `collect`).
   - Tab **Stages**: Klik salah satu stage untuk melihat diagram visual **DAG (*Directed Acyclic Graph*)**.
   - Tab **Executors**: Menampilkan ringkasan resource driver dan executor.
   - Tab **Storage**: Menampilkan RDD yang di-cache (`dataCache`) dengan ukuran memori RAM (contoh: 304 B) dan level *Memory Deserialized 1x Replicated*.

### 7.4 Mengakhiri Sesi Spark
1. Di prompt `scala>`: ketik `:quit`
2. Di bash kontainer: ketik `exit`

---

## 8. MATRIKS PERINTAH CEPAT (CHEAT SHEET CLI)

| Kategori | Perintah CMD / Bash | Fungsi |
|---|---|---|
| **Docker** | `docker compose up -d` | Menyalakan 9 kontainer klaster Big Data |
| **Docker** | `docker ps` | Memeriksa seluruh kontainer yang aktif |
| **Docker** | `docker compose down` | Mematikan seluruh kontainer klaster |
| **Docker** | `docker cp [file] namenode:/tmp/` | Menyalin file dari host Windows ke kontainer NameNode |
| **HDFS** | `hdfs dfsadmin -report` | Cek status kesehatan DataNode HDFS |
| **HDFS** | `hdfs dfs -mkdir -p [path]` | Membuat folder baru di HDFS |
| **HDFS** | `hdfs dfs -put -f [src] [dest]` | Unggah file ke HDFS (overwrite jika ada) |
| **HDFS** | `hdfs dfs -ls -R [path]` | Menampilkan seluruh isi folder HDFS |
| **HDFS** | `hdfs dfs -cat [path]` | Membaca isi file teks di HDFS |
| **HDFS** | `hdfs dfs -rm -r [path]` | Menghapus folder/file di HDFS |
| **HDFS** | `hdfs fsck [path] -files -blocks -locations` | Audit penempatan block dan replikasi file |
| **MapReduce** | `javac -classpath "$(/opt/hadoop/bin/hadoop classpath)" -d classes [file.java]` | Kompilasi source code Java MapReduce |
| **MapReduce** | `jar -cvf [app.jar] -C classes/ .` | Memaketkan class file menjadi arsip JAR |
| **YARN** | `yarn jar [app.jar] [MainClass] [in] [out]` | Menjalankan job MapReduce ke YARN |
| **YARN** | `yarn node -list` | Menampilkan seluruh NodeManager YARN |
| **Spark** | `/opt/spark/bin/spark-shell --master spark://spark-master:7077` | Membuka konsol interaktif Spark Shell Scala |
| **Spark Shell** | `:quit` | Keluar dari konsol spark-shell |

---

## 9. PANDUAN PEMECAHAN MASALAH (TROUBLESHOOTING SAAT UJIAN PRAKTIKUM)

### 1. Galat: `Output directory ... already exists` pada MapReduce
- **Penyebab:** Framework Hadoop melarang penggunaan folder output yang sudah ada demi menjaga integritas data.
- **Solusi Cepat:** Hapus folder output sebelum menjalankan job:
  ```bash
  hdfs dfs -rm -r /praktikum_Muhammad_Anwar_Ismail/hdfs/output
  ```

### 2. Galat: `ClassNotFoundException: org.apache.hadoop...` pada MapReduce
- **Penyebab:** Variabel `HADOOP_MAPRED_HOME` belum dikenali oleh NodeManager.
- **Solusi Cepat:** Pastikan file `mapred-site.xml` memuat properti:
  ```xml
  <property>
    <name>yarn.app.mapreduce.am.env</name>
    <value>HADOOP_MAPRED_HOME=/opt/hadoop</value>
  </property>
  ```

### 3. Galat: `Name node is in safe mode`
- **Penyebab:** NameNode sedang memvalidasi block saat startup dan mengunci sistem berkas dalam mode baca saja (*read-only*).
- **Solusi Cepat:** Paksa keluar dari safe mode:
  ```bash
  hdfs dfsadmin -safemode leave
  ```

### 4. Galat: `UnknownHostException: namenode` pada Spark
- **Penyebab:** Kontainer Spark belum berada di jaringan Docker yang sama dengan kontainer Hadoop.
- **Solusi Cepat:** Hubungkan kontainer Spark ke jaringan yang sama dengan perintah:
  ```cmd
  docker network connect mapreduce_default spark-master
  ```
  *(Atau jika menggunakan `docker-compose.yml` terpadu, masalah ini otomatis tidak terjadi).*

### 5. Galat: Halaman `http://localhost:4040` tidak bisa dibuka
- **Penyebab 1:** Sesi `spark-shell` sudah ditutup (port 4040 bersifat sesi aktif).
- **Penyebab 2:** Port 4040 belum dipetakan di file compose.
- **Solusi Cepat:** Pastikan `spark-shell` masih menyala di terminal dan baris `- "4040:4040"` ada di bawah service `spark-master`.

---

## 10. VARIASI SKENARIO SOAL UJIAN DAN POLA SOLUSI

### Skenario 1: Dosen Meminta Filter Kata Tertentu (Stopwords) pada MapReduce Java
Di dalam method `map()` pada `WordCount.java`, tambahkan kondisi:
```java
String token = itr.nextToken().toLowerCase();
if (!token.equals("dan") && !token.equals("yang") && !token.equals("di")) {
    word.set(token);
    context.write(word, one);
}
```

### Skenario 2: Dosen Meminta Menghitung Rata-rata Angka pada Spark
Jika diberikan dataset angka, hitung total dan jumlah elemen menggunakan kombinasi transformasi dan aksi:
```scala
val angka = sc.parallelize(Seq(10, 20, 30, 40, 50, 60))
val total = angka.reduce((a, b) => a + b)
val count = angka.count()
val rataRata = total.toDouble / count
println(s"Total: $total, Jumlah Data: $count, Rata-rata: $rataRata")
```

### Skenario 3: Dosen Meminta Filter dan Pengelompokan Berdasarkan Huruf Awalan pada Spark
```scala
val daftarKata = sc.parallelize(Seq("apel", "anggur", "belimbing", "ceri", "alpukat", "pisang"))
// Filter kata yang berawalan huruf 'a'
val kataA = daftarKata.filter(w => w.startsWith("a"))
kataA.collect() // Hasil: Array("apel", "anggur", "alpukat")

// Mengelompokkan berdasarkan panjang karakter kata
val panjangKata = daftarKata.map(w => (w.length, w)).groupByKey()
panjangKata.collect()
```

### Skenario 4: Dosen Memberikan Berkas CSV dan Meminta Membaca Kolom Tertentu
```scala
val csvData = sc.textFile("hdfs://namenode:8020/praktikum_Muhammad_Anwar_Ismail/hdfs/input/data.csv")
// Misalnya data format: NIM,Nama,Nilai -> ambil kolom Nilai (kolom ke-3)
val nilaiMahasiswa = csvData.map(line => {
  val kolom = line.split(",")
  kolom(2).toDouble
})
val rataNilai = nilaiMahasiswa.reduce(_ + _) / nilaiMahasiswa.count()
```
