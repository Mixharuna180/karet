# Aplikasi Laporan Keuangan Karet

Aplikasi ini dirancang untuk memantau dan melaporkan penjualan karet, strategi risiko, realisasi anggaran, dan perbandingan harga SICOM x SIR 20.

## Fitur Utama

- **Pelaporan Penjualan Karet**: Pantau penjualan karet, termasuk volume, harga, keuntungan, dan rekomendasi.
- **Strategi Risiko**: Kelola strategi risiko dengan identifikasi aspek, risiko, dan solusi.
- **Realisasi Anggaran**: Lacak aliran kas masuk dan keluar dengan visualisasi grafik.
- **Perbandingan Harga SICOM x SIR 20**: Analisis harga tertinggi dan terendah dengan perbandingan historis.
- **Ekspor PDF**: Buat laporan dalam format PDF dengan tabel dan visualisasi grafik.

## Instalasi

### Metode Satu Klik

1. Clone repositori ini:
   ```
   git clone https://github.com/Mixharuna180/karet.git
   cd karet
   ```

2. Jalankan script instalasi:
   ```
   ./app.sh
   ```

### Instalasi Manual

1. Clone repositori ini:
   ```
   git clone https://github.com/Mixharuna180/karet.git
   cd karet
   ```

2. Buat dan aktifkan virtual environment:
   ```
   python3 -m venv venv
   source venv/bin/activate  # Untuk Linux/Mac
   # atau
   venv\Scripts\activate  # Untuk Windows
   ```

3. Instal dependensi:
   ```
   pip install streamlit pandas matplotlib numpy plotly psycopg2-binary sqlalchemy reportlab statsmodels
   ```

4. Siapkan database PostgreSQL:
   - Buat database dan user PostgreSQL
   - Ekspor variabel lingkungan berikut:
     ```
     export DATABASE_URL="postgresql://user:password@localhost:5432/dbname"
     export PGDATABASE="dbname"
     export PGUSER="user"
     export PGPASSWORD="password"
     export PGHOST="localhost"
     export PGPORT="5432"
     ```

5. Buat konfigurasi Streamlit:
   ```
   mkdir -p .streamlit
   echo '[server]
   headless = true
   address = "0.0.0.0"
   port = 5000' > .streamlit/config.toml
   ```

6. Jalankan aplikasi:
   ```
   streamlit run app.py --server.port 5000
   ```

## Penggunaan

### Akses Aplikasi

Buka browser dan navigasikan ke `http://localhost:5000`

### Autentikasi

Untuk fitur editing data, gunakan password: `karet123`

### Tab dan Fungsionalitas

1. **Penjualan Karet**: Input dan lihat data penjualan karet.
2. **Strategi & Risiko**: Kelola strategi risiko perusahaan.
3. **Realisasi Anggaran**: Catat dan visualisasikan aliran kas.
4. **Harga SICOM x SIR 20**: Analisis perbandingan harga karet.

### Ekspor PDF

Setiap tab memiliki fungsi untuk mengekspor data ke PDF dengan grafik dan tabel yang relevan.

## Struktur Database

- `perusahaan`: Data perusahaan karet
- `penjualan_karet`: Transaksi penjualan karet
- `strategi_risiko`: Strategi mengelola risiko
- `realisasi_anggaran`: Arus kas perusahaan
- `harga_sicom_sir`: Data harga SICOM x SIR 20 (tertinggi/terendah)

## Kontribusi

Kontribusi selalu diterima! Silakan kirim pull request atau buka issue untuk diskusi fitur baru.

## Lisensi

[MIT License](LICENSE)