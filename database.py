import os
import streamlit as st
from sqlalchemy import create_engine, Column, Integer, Float, String, Date, ForeignKey, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import datetime

# Dapatkan connection string database dari environment variable
DATABASE_URL = os.environ.get("DATABASE_URL")

# Buat engine untuk koneksi ke database dengan parameter koneksi untuk menangani SSL issue
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    connect_args={
        'connect_timeout': 30,
        'keepalives': 1,
        'keepalives_idle': 30,
        'keepalives_interval': 10,
        'keepalives_count': 5
    }
)

# Buat base class untuk model SQLAlchemy
Base = declarative_base()

# Definisikan model/tabel
class Perusahaan(Base):
    __tablename__ = 'perusahaan'
    
    id = Column(Integer, primary_key=True)
    nama = Column(String, nullable=False)
    jenis = Column(String)  # Misalnya: Pabrik, Depo
    
    # Relationships
    penjualan_karet = relationship("PenjualanKaret", back_populates="perusahaan", cascade="all, delete-orphan")
    strategi_risiko = relationship("StrategiRisiko", back_populates="perusahaan", cascade="all, delete-orphan")
    realisasi_anggaran = relationship("RealisasiAnggaran", back_populates="perusahaan", cascade="all, delete-orphan")

class PenjualanKaret(Base):
    __tablename__ = 'penjualan_karet'
    
    id = Column(Integer, primary_key=True)
    perusahaan_id = Column(Integer, ForeignKey('perusahaan.id'), nullable=False)
    tanggal = Column(Date)
    jarak = Column(Float, default=0)  # dalam km
    harga_jual = Column(Float, default=0)  # per kg
    susut = Column(Float, default=0)  # dalam persen
    harga_beli = Column(Float, default=0)  # per kg
    berat_awal = Column(Float, default=0)  # dalam kg
    berat_jual = Column(Float, default=0)  # dalam kg
    total_harga_jual = Column(Float, default=0)
    total_harga_beli = Column(Float, default=0)
    keuntungan_kotor = Column(Float, default=0)
    ongkos_kirim = Column(Float, default=0)
    keuntungan_bersih = Column(Float, default=0)
    rekomendasi = Column(String)
    
    # Relationship
    perusahaan = relationship("Perusahaan", back_populates="penjualan_karet")

class StrategiRisiko(Base):
    __tablename__ = 'strategi_risiko'
    
    id = Column(Integer, primary_key=True)
    perusahaan_id = Column(Integer, ForeignKey('perusahaan.id'), nullable=False)
    aspek = Column(String)
    risiko = Column(String)
    solusi = Column(String)
    
    # Relationship
    perusahaan = relationship("Perusahaan", back_populates="strategi_risiko")

class RealisasiAnggaran(Base):
    __tablename__ = 'realisasi_anggaran'
    
    id = Column(Integer, primary_key=True)
    perusahaan_id = Column(Integer, ForeignKey('perusahaan.id'), nullable=False)
    tanggal = Column(Date)
    debet = Column(Float, default=0)  # uang masuk
    kredit = Column(Float, default=0)  # uang keluar
    saldo = Column(Float, default=0)  # saldo akhir
    volume = Column(String)  # misalnya: "1 Lot", "323 kg"
    keterangan = Column(String)
    
    # Relationship
    perusahaan = relationship("Perusahaan", back_populates="realisasi_anggaran")

# Buat tabel di database jika belum ada
Base.metadata.create_all(engine)

# Buat sessionmaker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Function untuk mendapatkan session database dengan penanganan error
def get_db_session():
    db = SessionLocal()
    try:
        # Test koneksi dengan melakukan query sederhana
        db.execute(text("SELECT 1"))
        return db
    except Exception as e:
        db.close()
        print(f"Error saat koneksi ke database: {e}")
        raise
    finally:
        # db.close() dipanggil di fungsi yang menggunakan get_db_session
        pass

# Function untuk menyimpan dan mendapatkan data penjualan karet
def tambah_perusahaan(nama, jenis=None):
    """
    Menambahkan perusahaan baru ke database
    """
    db = get_db_session()
    
    new_company = Perusahaan(
        nama=nama,
        jenis=jenis
    )
    
    db.add(new_company)
    db.commit()
    db.refresh(new_company)
    
    return new_company.id

def get_perusahaan():
    """
    Mendapatkan semua perusahaan
    """
    db = get_db_session()
    return db.query(Perusahaan).all()

def get_perusahaan_by_id(perusahaan_id):
    """
    Mendapatkan perusahaan berdasarkan ID
    """
    db = get_db_session()
    return db.query(Perusahaan).filter(Perusahaan.id == perusahaan_id).first()

def simpan_penjualan_karet(perusahaan_id, tanggal, jarak, harga_jual, susut, harga_beli, 
                          berat_awal, berat_jual, total_harga_jual, total_harga_beli, 
                          keuntungan_kotor, ongkos_kirim, keuntungan_bersih, rekomendasi):
    """
    Menyimpan data penjualan karet
    """
    db = get_db_session()
    
    # Cek apakah data sudah ada
    existing_data = db.query(PenjualanKaret).filter(
        PenjualanKaret.perusahaan_id == perusahaan_id,
        PenjualanKaret.tanggal == tanggal
    ).first()
    
    if existing_data:
        # Update data yang sudah ada
        existing_data.jarak = jarak
        existing_data.harga_jual = harga_jual
        existing_data.susut = susut
        existing_data.harga_beli = harga_beli
        existing_data.berat_awal = berat_awal
        existing_data.berat_jual = berat_jual
        existing_data.total_harga_jual = total_harga_jual
        existing_data.total_harga_beli = total_harga_beli
        existing_data.keuntungan_kotor = keuntungan_kotor
        existing_data.ongkos_kirim = ongkos_kirim
        existing_data.keuntungan_bersih = keuntungan_bersih
        existing_data.rekomendasi = rekomendasi
    else:
        # Buat data baru
        new_data = PenjualanKaret(
            perusahaan_id=perusahaan_id,
            tanggal=tanggal,
            jarak=jarak,
            harga_jual=harga_jual,
            susut=susut,
            harga_beli=harga_beli,
            berat_awal=berat_awal,
            berat_jual=berat_jual,
            total_harga_jual=total_harga_jual,
            total_harga_beli=total_harga_beli,
            keuntungan_kotor=keuntungan_kotor,
            ongkos_kirim=ongkos_kirim,
            keuntungan_bersih=keuntungan_bersih,
            rekomendasi=rekomendasi
        )
        db.add(new_data)
    
    db.commit()

def get_penjualan_karet(perusahaan_id=None):
    """
    Mendapatkan data penjualan karet
    """
    db = get_db_session()
    query = db.query(PenjualanKaret)
    
    if perusahaan_id:
        query = query.filter(PenjualanKaret.perusahaan_id == perusahaan_id)
    
    return query.all()

def get_penjualan_karet_by_id(id):
    """
    Mendapatkan data penjualan karet berdasarkan ID
    """
    db = get_db_session()
    return db.query(PenjualanKaret).filter(PenjualanKaret.id == id).first()

def hapus_penjualan_karet(id, perusahaan_id):
    """
    Menghapus data penjualan karet berdasarkan ID
    """
    db = get_db_session()
    try:
        penjualan_karet = db.query(PenjualanKaret).filter(
            PenjualanKaret.id == id, 
            PenjualanKaret.perusahaan_id == perusahaan_id
        ).first()
        
        if not penjualan_karet:
            raise Exception("Data penjualan karet tidak ditemukan")
        
        db.delete(penjualan_karet)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

# Function untuk menyimpan dan mendapatkan data strategi risiko
def simpan_strategi_risiko(perusahaan_id, aspek, risiko, solusi):
    """
    Menyimpan data strategi risiko
    """
    db = get_db_session()
    
    # Cek apakah data sudah ada
    existing_data = db.query(StrategiRisiko).filter(
        StrategiRisiko.perusahaan_id == perusahaan_id,
        StrategiRisiko.aspek == aspek
    ).first()
    
    if existing_data:
        # Update data yang sudah ada
        existing_data.risiko = risiko
        existing_data.solusi = solusi
    else:
        # Buat data baru
        new_data = StrategiRisiko(
            perusahaan_id=perusahaan_id,
            aspek=aspek,
            risiko=risiko,
            solusi=solusi
        )
        db.add(new_data)
    
    db.commit()

def get_strategi_risiko(perusahaan_id=None):
    """
    Mendapatkan data strategi risiko
    """
    db = get_db_session()
    query = db.query(StrategiRisiko)
    
    if perusahaan_id:
        query = query.filter(StrategiRisiko.perusahaan_id == perusahaan_id)
    
    return query.all()

# Function untuk menyimpan dan mendapatkan data realisasi anggaran
def simpan_realisasi_anggaran(perusahaan_id, tanggal, debet, kredit, saldo, volume, keterangan):
    """
    Menyimpan data realisasi anggaran dan rekalkukasi saldo
    """
    db = get_db_session()
    
    # Cek apakah data sudah ada
    existing_data = db.query(RealisasiAnggaran).filter(
        RealisasiAnggaran.perusahaan_id == perusahaan_id,
        RealisasiAnggaran.tanggal == tanggal,
        RealisasiAnggaran.keterangan == keterangan
    ).first()
    
    # Dapatkan transaksi sebelum tanggal ini untuk menghitung saldo awal
    previous_transactions = db.query(RealisasiAnggaran).filter(
        RealisasiAnggaran.perusahaan_id == perusahaan_id,
        RealisasiAnggaran.tanggal < tanggal
    ).order_by(RealisasiAnggaran.tanggal).all()
    
    # Hitung saldo awal dari transaksi sebelumnya
    previous_saldo = 0
    if previous_transactions:
        previous_saldo = previous_transactions[-1].saldo
    
    # Saldo baru = saldo sebelumnya + debet - kredit
    new_saldo = previous_saldo + debet - kredit
    
    if existing_data:
        # Update data yang sudah ada
        existing_data.debet = debet
        existing_data.kredit = kredit
        existing_data.saldo = new_saldo  # Gunakan saldo yang baru dihitung
        existing_data.volume = volume
    else:
        # Buat data baru
        new_data = RealisasiAnggaran(
            perusahaan_id=perusahaan_id,
            tanggal=tanggal,
            debet=debet,
            kredit=kredit,
            saldo=new_saldo,  # Gunakan saldo yang baru dihitung
            volume=volume,
            keterangan=keterangan
        )
        db.add(new_data)
    
    # Perbarui saldo untuk semua transaksi setelah tanggal ini
    next_transactions = db.query(RealisasiAnggaran).filter(
        RealisasiAnggaran.perusahaan_id == perusahaan_id,
        RealisasiAnggaran.tanggal > tanggal
    ).order_by(RealisasiAnggaran.tanggal).all()
    
    running_saldo = new_saldo
    for tx in next_transactions:
        running_saldo = running_saldo + tx.debet - tx.kredit
        tx.saldo = running_saldo
    
    db.commit()
    
    return new_saldo  # Mengembalikan saldo yang baru dihitung

def get_realisasi_anggaran(perusahaan_id=None):
    """
    Mendapatkan data realisasi anggaran diurutkan berdasarkan tanggal
    """
    db = get_db_session()
    query = db.query(RealisasiAnggaran)
    
    if perusahaan_id:
        query = query.filter(RealisasiAnggaran.perusahaan_id == perusahaan_id)
    
    # Mengembalikan hasil yang sudah diurutkan berdasarkan tanggal
    return query.order_by(RealisasiAnggaran.tanggal).all()

def get_realisasi_anggaran_by_id(id):
    """
    Mendapatkan data realisasi anggaran berdasarkan ID
    """
    db = get_db_session()
    return db.query(RealisasiAnggaran).filter(RealisasiAnggaran.id == id).first()

def hapus_realisasi_anggaran(id, perusahaan_id):
    """
    Menghapus data realisasi anggaran berdasarkan ID
    dan memperbarui saldo untuk entri berikutnya
    """
    db = get_db_session()
    
    # Cari data yang akan dihapus
    data_to_delete = db.query(RealisasiAnggaran).filter(RealisasiAnggaran.id == id).first()
    
    if not data_to_delete:
        raise Exception("Data tidak ditemukan")
    
    # Dapatkan tanggal data yang akan dihapus untuk memperbarui entri berikutnya
    tanggal = data_to_delete.tanggal
    
    # Hapus data
    db.delete(data_to_delete)
    db.commit()
    
    # Perbarui saldo untuk semua transaksi setelah tanggal ini
    transactions = db.query(RealisasiAnggaran).filter(
        RealisasiAnggaran.perusahaan_id == perusahaan_id,
    ).order_by(RealisasiAnggaran.tanggal).all()
    
    # Rekalkukasi semua saldo dari awal
    running_saldo = 0
    for tx in transactions:
        running_saldo = running_saldo + tx.debet - tx.kredit
        tx.saldo = running_saldo
    
    db.commit()
    
    return True

# Inisialisasi database dengan data penjualan karet
def init_db_with_karet_data():
    db = get_db_session()
    
    # Cek apakah ada perusahaan
    companies = db.query(Perusahaan).all()
    
    if not companies:
        # Buat perusahaan untuk laporan karet
        depo_cinta_manis = Perusahaan(
            nama="Depo Cinta Manis",
            jenis="Depo"
        )
        pabrik_abp = Perusahaan(
            nama="Pabrik ABP",
            jenis="Pabrik"
        )
        pabrik_bgp = Perusahaan(
            nama="Pabrik BGP",
            jenis="Pabrik"
        )
        pabrik_bap = Perusahaan(
            nama="Pabrik BAP",
            jenis="Pabrik"
        )
        
        db.add_all([depo_cinta_manis, pabrik_abp, pabrik_bgp, pabrik_bap])
        db.commit()
        
        # Refresh objects untuk mendapatkan ID
        db.refresh(depo_cinta_manis)
        db.refresh(pabrik_abp)
        db.refresh(pabrik_bgp)
        db.refresh(pabrik_bap)
        
        # Tambahkan data penjualan karet dari contoh
        tanggal = datetime.date(2025, 4, 15)  # Tanggal contoh
        
        # Data untuk Depo Cinta Manis
        penjualan_dcm = PenjualanKaret(
            perusahaan_id=depo_cinta_manis.id,
            tanggal=tanggal,
            jarak=45,
            harga_jual=13700,
            susut=10,
            harga_beli=11500,
            berat_awal=2000,
            berat_jual=1800,
            total_harga_jual=24660000,
            total_harga_beli=23000000,
            keuntungan_kotor=1660000,
            ongkos_kirim=1000000,
            keuntungan_bersih=660000,
            rekomendasi="Kurang menguntungkan karena harga jual lebih rendah."
        )
        
        # Data untuk Pabrik ABP
        penjualan_abp = PenjualanKaret(
            perusahaan_id=pabrik_abp.id,
            tanggal=tanggal,
            jarak=112,
            harga_jual=15700,
            susut=13,
            harga_beli=11500,
            berat_awal=2000,
            berat_jual=1740,
            total_harga_jual=27318000,
            total_harga_beli=23000000,
            keuntungan_kotor=4318000,
            ongkos_kirim=1200000,
            keuntungan_bersih=3118000,
            rekomendasi="Paling menguntungkan dengan profit terbesar."
        )
        
        # Data untuk Pabrik BGP
        penjualan_bgp = PenjualanKaret(
            perusahaan_id=pabrik_bgp.id,
            tanggal=tanggal,
            jarak=132,
            harga_jual=15800,
            susut=14,
            harga_beli=11500,
            berat_awal=2000,
            berat_jual=1720,
            total_harga_jual=27176000,
            total_harga_beli=23000000,
            keuntungan_kotor=4176000,
            ongkos_kirim=1300000,
            keuntungan_bersih=2876000,
            rekomendasi="Alternatif terbaik setelah Pabrik B."
        )
        
        # Data untuk Pabrik BAP
        penjualan_bap = PenjualanKaret(
            perusahaan_id=pabrik_bap.id,
            tanggal=tanggal,
            jarak=143,
            harga_jual=15100,
            susut=17,
            harga_beli=11500,
            berat_awal=2000,
            berat_jual=1660,
            total_harga_jual=25398000,
            total_harga_beli=23000000,
            keuntungan_kotor=2398000,
            ongkos_kirim=1500000,
            keuntungan_bersih=898000,
            rekomendasi="Kurang direkomendasikan karena jarak terlalu jauh dan susut tinggi."
        )
        
        db.add_all([penjualan_dcm, penjualan_abp, penjualan_bgp, penjualan_bap])
        
        # Tambahkan data strategi risiko
        strategi_risiko = [
            StrategiRisiko(
                perusahaan_id=pabrik_abp.id,
                aspek="Penyusutan Berlebih",
                risiko="Jika susut lebih dari estimasi, profit bisa menurun",
                solusi="Gunakn transportasi cepat dan tertutup, pastikan karet tidak terlalu lama dalam Perjalanan dan terpapar matahari"
            ),
            StrategiRisiko(
                perusahaan_id=pabrik_abp.id,
                aspek="Fluktuasi Harga Pasar",
                risiko="Jika harga jual turun, profit bisa berkurang.",
                solusi="Negosiasi kontrak harga tetap. Fokus menjual saat harga pasar stabil atau naik."
            ),
            StrategiRisiko(
                perusahaan_id=pabrik_abp.id,
                aspek="Biaya Transportasi Tinggi",
                risiko="Biaya pengiriman memengaruhi profitabilitas.",
                solusi="Kirim dalam volume besar untuk menekan biaya. Cari rute tercepat dan efisien. Kolaborasi dengan pengangkut untuk mendapatkan harga lebih murah."
            )
        ]
        
        db.add_all(strategi_risiko)
        
        # Tambahkan data realisasi anggaran
        realisasi_anggaran = [
            RealisasiAnggaran(
                perusahaan_id=pabrik_abp.id,
                tanggal=datetime.date(2025, 2, 6),
                debet=1000000,
                kredit=0,
                saldo=1000000,
                volume="1 Lot",
                keterangan="Kredit Kas"
            ),
            RealisasiAnggaran(
                perusahaan_id=pabrik_abp.id,
                tanggal=datetime.date(2025, 2, 6),
                debet=0,
                kredit=859000,
                saldo=141000,
                volume="1 Pcs",
                keterangan="Beli Timbangan Duduk 150 Kg"
            ),
            RealisasiAnggaran(
                perusahaan_id=pabrik_abp.id,
                tanggal=datetime.date(2025, 2, 9),
                debet=10000000,
                kredit=0,
                saldo=10141000,  # Saldo yang sudah benar: 141000 + 10000000 = 10141000
                volume="1 Lot",
                keterangan="Kredit KAS"
            )
        ]
        
        db.add_all(realisasi_anggaran)
        db.commit()
        
        print("Database diinisialisasi dengan data penjualan karet")
        return pabrik_abp.id
    
    return companies[0].id

# Fungsi untuk memperbaiki saldo pada seluruh data realisasi anggaran
def fix_all_realisasi_anggaran_saldo():
    """
    Memperbaiki semua saldo pada realisasi anggaran untuk memastikan
    kalkulasi berjalan dengan benar
    """
    db = get_db_session()
    
    # Dapatkan semua perusahaan
    companies = db.query(Perusahaan).all()
    
    for company in companies:
        # Dapatkan semua transaksi untuk perusahaan ini
        transactions = db.query(RealisasiAnggaran).filter(
            RealisasiAnggaran.perusahaan_id == company.id
        ).order_by(RealisasiAnggaran.tanggal).all()
        
        # Rekalkukasi saldo untuk setiap transaksi
        running_saldo = 0
        for tx in transactions:
            running_saldo = running_saldo + tx.debet - tx.kredit
            if tx.saldo != running_saldo:
                tx.saldo = running_saldo
                print(f"Memperbaiki saldo untuk transaksi {tx.id}: {tx.keterangan}, tanggal {tx.tanggal}")
    
    # Simpan perubahan
    db.commit()
    print("Proses perbaikan saldo selesai.")

# Jalankan inisialisasi database
try:
    default_perusahaan_id = init_db_with_karet_data()
    # Jalankan juga perbaikan saldo
    fix_all_realisasi_anggaran_saldo()
except Exception as e:
    print(f"Error saat inisialisasi database: {e}")
    default_perusahaan_id = None