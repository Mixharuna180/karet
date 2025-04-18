#!/bin/bash

echo "==================================================="
echo "     INSTALASI APLIKASI LAPORAN KEUANGAN KARET     "
echo "==================================================="
echo "Memulai instalasi aplikasi..."

# Periksa apakah Python terinstal
if ! command -v python3 &> /dev/null; then
    echo "Python3 tidak ditemukan. Menginstal Python3..."
    sudo apt-get update
    sudo apt-get install -y python3 python3-pip python3-venv
    if [ $? -ne 0 ]; then
        echo "Gagal menginstal Python3. Silakan coba menginstal secara manual."
        exit 1
    fi
fi

echo "Membuat virtual environment..."
python3 -m venv venv
source venv/bin/activate

echo "Menginstal dependensi Python..."
pip install --upgrade pip

# Pastikan Streamlit diinstal terlebih dahulu
echo "Menginstal Streamlit..."
pip install streamlit>=1.27.0

# Install dependensi lainnya
echo "Menginstal dependensi aplikasi lainnya..."
# Install from pyproject.toml untuk memastikan versi yang kompatibel
if [ -f "pyproject.toml" ]; then
    pip install -e .
else
    # Fallback jika pyproject.toml tidak ada
    pip install pandas>=2.0.0 matplotlib>=3.7.0 numpy>=1.24.0 plotly>=5.15.0 psycopg2-binary>=2.9.5 sqlalchemy>=2.0.0 reportlab>=3.6.0 statsmodels>=0.14.0
fi

# Verifikasi instalasi Streamlit
if ! command -v streamlit &> /dev/null; then
    echo "Streamlit gagal diinstal. Mencoba menginstal ulang..."
    pip install --force-reinstall streamlit>=1.27.0
    if ! command -v streamlit &> /dev/null; then
        echo "PERINGATAN: Gagal menginstal Streamlit. Aplikasi mungkin tidak akan berjalan dengan benar."
    fi
fi

# Memeriksa apakah PostgreSQL terinstal
if ! command -v psql &> /dev/null; then
    echo "PostgreSQL tidak ditemukan. Menginstal PostgreSQL..."
    sudo apt-get update
    sudo apt-get install -y postgresql postgresql-contrib
    
    if [ $? -ne 0 ]; then
        echo "Gagal menginstal PostgreSQL. Silakan coba menginstal secara manual."
        exit 1
    fi
    
    # Memulai layanan PostgreSQL
    sudo service postgresql start
fi

# Membuat database dan user PostgreSQL jika belum ada
echo "Menyiapkan database PostgreSQL..."
DB_NAME="karet_db"
DB_USER="karet_user"
DB_PASSWORD="karet123" # Bisa diganti dengan password yang lebih aman

if sudo -u postgres psql -lqt | cut -d \| -f 1 | grep -qw $DB_NAME; then
    echo "Database $DB_NAME sudah ada."
else
    echo "Membuat database baru: $DB_NAME..."
    sudo -u postgres psql -c "CREATE DATABASE $DB_NAME;"
    sudo -u postgres psql -c "CREATE USER $DB_USER WITH ENCRYPTED PASSWORD '$DB_PASSWORD';"
    sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"
    
    # Export variabel lingkungan untuk koneksi database
    export DATABASE_URL="postgresql://$DB_USER:$DB_PASSWORD@localhost:5432/$DB_NAME"
    
    # Simpan konfigurasi database ke file .env
    echo "DATABASE_URL=postgresql://$DB_USER:$DB_PASSWORD@localhost:5432/$DB_NAME" > .env
    echo "PGDATABASE=$DB_NAME" >> .env
    echo "PGUSER=$DB_USER" >> .env
    echo "PGPASSWORD=$DB_PASSWORD" >> .env
    echo "PGHOST=localhost" >> .env
    echo "PGPORT=5432" >> .env
    
    echo "Konfigurasi database disimpan ke file .env"
fi

# Membuat direktori .streamlit jika belum ada
mkdir -p .streamlit

# Membuat file konfigurasi Streamlit
echo "Menyiapkan konfigurasi Streamlit..."
cat > .streamlit/config.toml << EOF
[server]
headless = true
address = "0.0.0.0"
port = 5000
EOF

echo "==================================================="
echo "            INSTALASI SELESAI!                    "
echo "==================================================="
echo "Cara menjalankan aplikasi:"
echo "1. Aktifkan virtual environment: source venv/bin/activate"
echo "2. Jalankan aplikasi: streamlit run app.py --server.port 5000"
echo "==================================================="
echo "Cara mengatasi masalah umum:"
echo "- Error koneksi database: Pastikan PostgreSQL berjalan dengan 'sudo service postgresql status'"
echo "- Streamlit tidak terpasang: Jalankan 'pip install streamlit>=1.27.0'"
echo "- Dependensi tertinggal: Jalankan 'pip install -r requirements.txt' jika ada"
echo "- Error port: Pastikan port 5000 tidak digunakan oleh aplikasi lain"
echo "==================================================="
echo "Memulai aplikasi sekarang..."

# Jalankan aplikasi
streamlit run app.py --server.port 5000 || {
  echo "==================================================="
  echo "ERROR: Aplikasi gagal dijalankan!"
  echo "Periksa pesan error di atas dan lihat dokumentasi untuk mengatasi masalah."
  echo "Atau buka README.md untuk panduan lebih lanjut."
  echo "==================================================="
  exit 1
}