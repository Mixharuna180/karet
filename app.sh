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
# Install from pyproject.toml untuk memastikan versi yang kompatibel
if [ -f "pyproject.toml" ]; then
    pip install -e .
else
    # Fallback jika pyproject.toml tidak ada
    pip install streamlit pandas matplotlib numpy plotly psycopg2-binary sqlalchemy reportlab statsmodels
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
echo "Memulai aplikasi sekarang..."

# Jalankan aplikasi
streamlit run app.py --server.port 5000