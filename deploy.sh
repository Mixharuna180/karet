#!/bin/bash

echo "==================================================="
echo "       SETUP DEPLOYMENT LAPORAN KEUANGAN KARET     "
echo "==================================================="
echo "Memulai konfigurasi deployment..."

# Periksa apakah script dijalankan sebagai root
if [ "$(id -u)" != "0" ]; then
   echo "Script ini harus dijalankan sebagai root atau dengan sudo." 
   exit 1
fi

# Periksa apakah Nginx terinstal
if ! command -v nginx &> /dev/null; then
    echo "Nginx tidak ditemukan. Menginstal Nginx..."
    apt-get update
    apt-get install -y nginx
    if [ $? -ne 0 ]; then
        echo "Gagal menginstal Nginx. Silakan coba menginstal secara manual."
        exit 1
    fi
fi

# Menginstal dependensi lain yang diperlukan
echo "Menginstal dependensi tambahan..."
apt-get install -y supervisor

# Membuat direktori untuk aplikasi jika belum ada
APP_DIR="/opt/karet_app"
if [ ! -d "$APP_DIR" ]; then
    echo "Membuat direktori aplikasi di $APP_DIR..."
    mkdir -p $APP_DIR
fi

# Menyalin file aplikasi ke direktori deployment
echo "Menyalin file aplikasi..."
cp -r ./* $APP_DIR/

# Mengatur kepemilikan direktori
echo "Mengatur kepemilikan direktori..."
chown -R www-data:www-data $APP_DIR

# Membuat virtual environment di direktori deployment
echo "Membuat virtual environment..."
cd $APP_DIR
python3 -m venv venv
source venv/bin/activate

# Menginstal dependensi
echo "Menginstal dependensi Python..."
pip install --upgrade pip
pip install streamlit>=1.27.0
if [ -f "pyproject.toml" ]; then
    pip install -e .
else
    pip install pandas>=2.0.0 matplotlib>=3.7.0 numpy>=1.24.0 plotly>=5.15.0 psycopg2-binary>=2.9.5 sqlalchemy>=2.0.0 reportlab>=3.6.0 statsmodels>=0.14.0
fi

# Membuat konfigurasi Nginx
echo "Membuat konfigurasi Nginx..."
cat > /etc/nginx/sites-available/karet-app << EOF
server {
    listen 80;
    server_name localhost;  # Ganti dengan domain Anda jika ada

    location / {
        proxy_pass http://localhost:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
        proxy_read_timeout 86400;
    }
}
EOF

# Mengaktifkan site Nginx
echo "Mengaktifkan konfigurasi Nginx..."
ln -sf /etc/nginx/sites-available/karet-app /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default  # Menghapus konfigurasi default

# Membuat konfigurasi supervisor
echo "Membuat konfigurasi supervisor..."
cat > /etc/supervisor/conf.d/karet-app.conf << EOF
[program:karet-app]
directory=$APP_DIR
command=$APP_DIR/venv/bin/streamlit run app.py --server.port=5000 --server.address=0.0.0.0 --server.headless=true
autostart=true
autorestart=true
stderr_logfile=/var/log/karet-app.err.log
stdout_logfile=/var/log/karet-app.out.log
user=www-data
environment=HOME="$APP_DIR",USER="www-data"
EOF

# Memuat ulang supervisor
echo "Memuat ulang konfigurasi supervisor..."
supervisorctl reload

# Restart Nginx
echo "Restart Nginx..."
systemctl restart nginx

# Membuat skrip untuk menjalankan dan menghentikan aplikasi
echo "Membuat skrip kontrol aplikasi..."
cat > $APP_DIR/start-app.sh << EOF
#!/bin/bash
supervisorctl start karet-app
EOF

cat > $APP_DIR/stop-app.sh << EOF
#!/bin/bash
supervisorctl stop karet-app
EOF

cat > $APP_DIR/restart-app.sh << EOF
#!/bin/bash
supervisorctl restart karet-app
EOF

# Membuat skrip executable
chmod +x $APP_DIR/start-app.sh
chmod +x $APP_DIR/stop-app.sh
chmod +x $APP_DIR/restart-app.sh

echo "==================================================="
echo "           DEPLOYMENT SELESAI!                     "
echo "==================================================="
echo "Aplikasi sekarang dapat diakses di:"
echo "- http://localhost (dari server)"
echo "- http://IP_SERVER (dari luar, ganti IP_SERVER dengan IP publik server)"
echo ""
echo "Skrip kontrol aplikasi:"
echo "- $APP_DIR/start-app.sh: Untuk memulai aplikasi"
echo "- $APP_DIR/stop-app.sh: Untuk menghentikan aplikasi"
echo "- $APP_DIR/restart-app.sh: Untuk memulai ulang aplikasi"
echo ""
echo "Log aplikasi:"
echo "- Error log: /var/log/karet-app.err.log"
echo "- Output log: /var/log/karet-app.out.log"
echo "==================================================="

# Memeriksa status aplikasi
echo "Status aplikasi:"
supervisorctl status karet-app