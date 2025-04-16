import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, date
import numpy as np
import base64
from utils import format_currency, format_percentage
from database import (
    get_perusahaan, get_perusahaan_by_id, tambah_perusahaan,
    get_penjualan_karet, simpan_penjualan_karet, get_penjualan_karet_by_id, hapus_penjualan_karet,
    get_strategi_risiko, simpan_strategi_risiko,
    get_realisasi_anggaran, simpan_realisasi_anggaran,
    get_realisasi_anggaran_by_id, hapus_realisasi_anggaran,
    fix_all_realisasi_anggaran_saldo
)
from pdf_generator import generate_pdf_penjualan_karet

# Set page configuration
st.set_page_config(
    page_title="Aplikasi Laporan Penjualan Karet",
    page_icon="🧪",
    layout="wide"
)

# Application title
st.title("Laporan Penjualan Karet")
st.markdown("---")

# Initialize session state variables if they don't exist
if 'selected_perusahaan_id' not in st.session_state:
    # Dapatkan daftar perusahaan dari database
    try:
        perusahaan_list = get_perusahaan()
        if perusahaan_list:
            # Pilih perusahaan pertama secara default
            st.session_state.selected_perusahaan_id = perusahaan_list[0].id
            st.session_state.selected_perusahaan_nama = perusahaan_list[0].nama
        else:
            st.session_state.selected_perusahaan_id = None
            st.session_state.selected_perusahaan_nama = ""
    except Exception as e:
        st.error(f"Terjadi kesalahan saat mengambil data perusahaan: {e}")
        perusahaan_list = []
        st.session_state.selected_perusahaan_id = None
        st.session_state.selected_perusahaan_nama = ""

# Inisialisasi variabel autentikasi
if 'is_authenticated' not in st.session_state:
    st.session_state.is_authenticated = False

# Kata sandi untuk akses edit data (dalam aplikasi nyata seharusnya disimpan dengan aman)
admin_password = "karet123"

# Sidebar for company selection and data input
with st.sidebar:
    st.header("Konfigurasi Laporan")
    
    # Autentikasi untuk akses edit
    st.subheader("Akses Admin")
    if not st.session_state.is_authenticated:
        with st.form("login_form"):
            password = st.text_input("Masukkan kata sandi", type="password")
            login_button = st.form_submit_button("Login")
            
            if login_button:
                if password == admin_password:
                    st.session_state.is_authenticated = True
                    st.success("Login berhasil!")
                    st.rerun()
                else:
                    st.error("Kata sandi salah!")
    else:
        st.success("Anda sudah login sebagai admin.")
        if st.button("Logout"):
            st.session_state.is_authenticated = False
            st.rerun()
    
    # Perusahaan Selection
    st.subheader("Pilih Perusahaan")
    
    # Dapatkan daftar perusahaan dari database
    try:
        perusahaan_list = get_perusahaan()
        perusahaan_names = [p.nama for p in perusahaan_list]
        perusahaan_ids = [p.id for p in perusahaan_list]
    except Exception as e:
        st.error(f"Terjadi kesalahan saat mengambil data perusahaan: {e}")
        perusahaan_list = []
        perusahaan_names = []
        perusahaan_ids = []
    
    # Tambahkan opsi untuk membuat perusahaan baru
    perusahaan_names.append("+ Tambah Perusahaan Baru")
    
    selected_perusahaan_index = st.selectbox(
        "Perusahaan", 
        range(len(perusahaan_names)), 
        format_func=lambda x: perusahaan_names[x]
    )
    
    # Jika user memilih untuk menambah perusahaan baru
    if selected_perusahaan_index == len(perusahaan_names) - 1:
        with st.form("new_perusahaan_form"):
            new_perusahaan_nama = st.text_input("Nama Perusahaan")
            new_perusahaan_jenis = st.selectbox("Jenis", ["Pabrik", "Depo"])
            
            submit_button = st.form_submit_button("Tambah Perusahaan")
            
            if submit_button and new_perusahaan_nama:
                new_perusahaan_id = tambah_perusahaan(new_perusahaan_nama, new_perusahaan_jenis)
                st.session_state.selected_perusahaan_id = new_perusahaan_id
                st.session_state.selected_perusahaan_nama = new_perusahaan_nama
                st.success(f"Perusahaan {new_perusahaan_nama} berhasil dibuat!")
                st.rerun()
    else:
        # Jika ada perusahaan, update selected_perusahaan_id di session_state
        if perusahaan_list:
            st.session_state.selected_perusahaan_id = perusahaan_ids[selected_perusahaan_index]
            st.session_state.selected_perusahaan_nama = perusahaan_names[selected_perusahaan_index]
    
    # Judul Laporan
    report_title = st.text_input("Judul Laporan", "Laporan Penjualan Karet")

# Main content area with tabs
tab1, tab2, tab3 = st.tabs([
    "Rencana Penjualan Karet", 
    "Strategi dan Risiko", 
    "Realisasi Anggaran"
])

# Tab 1: Rencana Penjualan Karet
with tab1:
    st.header("Rencana Penjualan Karet")
    
    # Get penjualan_karet data for the selected perusahaan
    if st.session_state.selected_perusahaan_id:
        penjualan_data = get_penjualan_karet(st.session_state.selected_perusahaan_id)
    else:
        penjualan_data = []
    
    # Display form to add new data
    with st.expander("Tambah/Edit Data Penjualan Karet", expanded=True):
        if not st.session_state.is_authenticated:
            st.warning("Silakan login sebagai admin di sidebar untuk menambah atau mengedit data")
        
        # Disable form jika belum terotentikasi
        form_disabled = not st.session_state.is_authenticated
        
        with st.form("penjualan_karet_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                tanggal = st.date_input("Tanggal", date.today())
                jarak = st.number_input("Jarak (km)", min_value=0.0, step=0.1)
                harga_jual = st.number_input("Harga Jual (Rp/kg)", min_value=0.0, step=100.0)
                susut = st.number_input("Susut (%)", min_value=0.0, max_value=100.0, step=0.1)
                harga_beli = st.number_input("Harga Beli (Rp/kg)", min_value=0.0, step=100.0)
            
            with col2:
                berat_awal = st.number_input("Berat Awal (kg)", min_value=0.0, step=10.0)
                # Calculate berat_jual based on susut
                berat_jual = berat_awal * (1 - susut/100)
                st.metric("Berat Jual (kg)", f"{berat_jual:.2f}")
                
                # Calculate totals
                total_harga_jual = harga_jual * berat_jual
                total_harga_beli = harga_beli * berat_awal
                keuntungan_kotor = total_harga_jual - total_harga_beli
                
                ongkos_kirim = st.number_input("Ongkos Kirim (Rp)", min_value=0.0, step=100000.0)
                keuntungan_bersih = keuntungan_kotor - ongkos_kirim
                
                st.metric("Total Harga Jual", format_currency(total_harga_jual))
                st.metric("Total Harga Beli", format_currency(total_harga_beli))
                st.metric("Keuntungan Kotor", format_currency(keuntungan_kotor))
                st.metric("Keuntungan Bersih", format_currency(keuntungan_bersih))
            
            rekomendasi = st.text_area("Rekomendasi", "")
            
            submit_button = st.form_submit_button("Simpan Data")
            
            if submit_button and st.session_state.selected_perusahaan_id:
                try:
                    simpan_penjualan_karet(
                        st.session_state.selected_perusahaan_id,
                        tanggal,
                        jarak,
                        harga_jual,
                        susut,
                        harga_beli,
                        berat_awal,
                        berat_jual,
                        total_harga_jual,
                        total_harga_beli,
                        keuntungan_kotor,
                        ongkos_kirim,
                        keuntungan_bersih,
                        rekomendasi
                    )
                    st.success("Data penjualan karet berhasil disimpan!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Terjadi kesalahan saat menyimpan data: {e}")
    
    # Display existing data in table
    if penjualan_data:
        st.subheader("Data Penjualan Karet")
        
        df_penjualan = pd.DataFrame([
            {
                "ID": p.id,
                "Tanggal": p.tanggal,
                "Jarak (km)": p.jarak,
                "Harga Jual (Rp/kg)": p.harga_jual,
                "Susut (%)": p.susut,
                "Harga Beli (Rp/kg)": p.harga_beli,
                "Berat Awal (kg)": p.berat_awal,
                "Berat Jual (kg)": p.berat_jual,
                "Total Harga Jual": p.total_harga_jual,
                "Total Harga Beli": p.total_harga_beli,
                "Keuntungan Kotor": p.keuntungan_kotor,
                "Ongkos Kirim": p.ongkos_kirim,
                "Keuntungan Bersih": p.keuntungan_bersih
            } for p in penjualan_data
        ])
        
        # Tampilkan tabel tanpa kolom ID
        st.dataframe(df_penjualan.drop(columns=["ID"]), use_container_width=True)
        
        # Fitur edit dan hapus data penjualan karet
        if st.session_state.is_authenticated:
            st.subheader("Edit/Hapus Data Penjualan Karet")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Pilih data untuk diedit/hapus
                selected_penjualan_id = st.selectbox(
                    "Pilih data untuk diedit/hapus", 
                    df_penjualan["ID"].tolist(),
                    format_func=lambda x: f"Tanggal: {df_penjualan[df_penjualan['ID']==x]['Tanggal'].values[0]} - Jarak: {df_penjualan[df_penjualan['ID']==x]['Jarak (km)'].values[0]} km"
                )
                
                # Tampilkan tombol hapus
                if st.button("🗑️ Hapus Data Penjualan", key="delete_penjualan_button", help="Hapus data penjualan karet yang dipilih"):
                    try:
                        hapus_penjualan_karet(selected_penjualan_id, st.session_state.selected_perusahaan_id)
                        st.success(f"Data penjualan karet berhasil dihapus!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Terjadi kesalahan saat menghapus data: {e}")
            
            # TODO: Tambahkan fitur untuk mengedit data penjualan karet di versi berikutnya
            # Karena banyak field, untuk saat ini pengguna bisa menghapus data dan membuat yang baru
        
        # Create table for recommendations
        st.subheader("Rekomendasi")
        
        # Define color based on profit
        def get_color_based_on_profit(profit):
            if profit > 3000000:
                return "green"
            elif profit > 1000000:
                return "orange"
            else:
                return "red"
        
        for p in penjualan_data:
            color = get_color_based_on_profit(p.keuntungan_bersih)
            st.markdown(f"""
            <div style="padding: 10px; border-left: 5px solid {color}; margin-bottom: 10px;">
                <h4>{get_perusahaan_by_id(p.perusahaan_id).nama}</h4>
                <p><strong>Keuntungan Bersih:</strong> {format_currency(p.keuntungan_bersih)}</p>
                <p>{p.rekomendasi}</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Visualizations
        st.subheader("Visualisasi")
        
        fig = px.bar(
            df_penjualan,
            x="Tanggal",
            y=["Keuntungan Kotor", "Ongkos Kirim", "Keuntungan Bersih"],
            title="Perbandingan Keuntungan per Penjualan",
            barmode="group"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Plot comparison between price and distance
        # Tambahkan kolom untuk nilai absolut keuntungan bersih untuk ukuran marker
        df_penjualan["Keuntungan_Bersih_Abs"] = np.abs(df_penjualan["Keuntungan Bersih"])
        
        # Gunakan nilai absolut untuk size dan nilai asli untuk color
        fig2 = px.scatter(
            df_penjualan,
            x="Jarak (km)",
            y="Harga Jual (Rp/kg)",
            size="Keuntungan_Bersih_Abs",  # Gunakan nilai absolut untuk ukuran
            color="Keuntungan Bersih",    # Tetap gunakan nilai asli untuk warna
            hover_name="Tanggal",
            title="Hubungan antara Jarak, Harga Jual, dan Keuntungan",
            size_max=50,  # Batasi ukuran maksimum marker
        )
        st.plotly_chart(fig2, use_container_width=True)
        
        # Plot susut vs distance - pastikan menggunakan nilai positif untuk ukuran marker
        fig3 = px.scatter(
            df_penjualan,
            x="Jarak (km)",
            y="Susut (%)",
            size="Berat Awal (kg)",  # Ini seharusnya selalu positif
            color="Keuntungan Bersih",
            hover_name="Tanggal",
            title="Hubungan antara Jarak dan Susut",
            size_max=40  # Batasi ukuran maksimum marker
        )
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.info("Belum ada data penjualan karet. Silakan tambahkan data baru menggunakan form di atas.")

# Tab 2: Strategi dan Risiko
with tab2:
    st.header("Strategi dan Risiko Pasar Penjualan Karet")
    
    # Get strategi_risiko data for the selected perusahaan
    if st.session_state.selected_perusahaan_id:
        strategi_data = get_strategi_risiko(st.session_state.selected_perusahaan_id)
    else:
        strategi_data = []
    
    # Display form to add new data
    with st.expander("Tambah Strategi dan Risiko", expanded=True):
        if not st.session_state.is_authenticated:
            st.warning("Silakan login sebagai admin di sidebar untuk menambah atau mengedit data")
            
        with st.form("strategi_risiko_form"):
            aspek = st.text_input("Aspek")
            risiko = st.text_area("Risiko")
            solusi = st.text_area("Solusi")
            
            submit_button = st.form_submit_button("Simpan Data")
            
            if submit_button and st.session_state.selected_perusahaan_id and aspek and risiko and solusi:
                try:
                    simpan_strategi_risiko(
                        st.session_state.selected_perusahaan_id,
                        aspek,
                        risiko,
                        solusi
                    )
                    st.success("Strategi dan risiko berhasil disimpan!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Terjadi kesalahan saat menyimpan data: {e}")
    
    # Display existing data in table
    if strategi_data:
        st.subheader("Data Strategi dan Risiko")
        
        df_strategi = pd.DataFrame([
            {
                "No": i+1,
                "Aspek": s.aspek,
                "Risiko": s.risiko,
                "Solusi": s.solusi
            } for i, s in enumerate(strategi_data)
        ])
        
        st.dataframe(df_strategi, use_container_width=True)
        
        # Display in a more readable format
        st.subheader("Strategi dan Risiko Penjualan Karet")
        
        for i, s in enumerate(strategi_data):
            st.markdown(f"""
            <div style="padding: 10px; border: 1px solid #ddd; border-radius: 5px; margin-bottom: 10px;">
                <h4>{i+1}. {s.aspek}</h4>
                <p><strong>Risiko:</strong> {s.risiko}</p>
                <p><strong>Solusi:</strong> {s.solusi}</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Belum ada data strategi dan risiko. Silakan tambahkan data baru menggunakan form di atas.")

# Tab 3: Realisasi Anggaran
with tab3:
    st.header("Realisasi Anggaran")
    
    # Get realisasi_anggaran data for the selected perusahaan
    if st.session_state.selected_perusahaan_id:
        anggaran_data = get_realisasi_anggaran(st.session_state.selected_perusahaan_id)
    else:
        anggaran_data = []
    
    # Display form to add new data
    with st.expander("Tambah Realisasi Anggaran", expanded=True):
        if not st.session_state.is_authenticated:
            st.warning("Silakan login sebagai admin di sidebar untuk menambah atau mengedit data")
            
        with st.form("realisasi_anggaran_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                tanggal = st.date_input("Tanggal", date.today(), key="anggaran_tanggal")
                debet = st.number_input("Debet (In)", min_value=0.0, step=100000.0)
                kredit = st.number_input("Kredit (Out)", min_value=0.0, step=100000.0)
            
            with col2:
                # Hitung saldo berdasarkan data terakhir yang diurutkan berdasarkan tanggal
                last_saldo = 0
                if anggaran_data:
                    sorted_data = sorted(anggaran_data, key=lambda x: x.tanggal)
                    # Ambil saldo terakhir dari data yang sudah ada
                    last_saldo = sorted_data[-1].saldo
                
                # Calculate new saldo
                saldo = last_saldo + debet - kredit
                st.metric("Saldo", format_currency(saldo))
                
                volume = st.text_input("Volume", "")
                keterangan = st.text_area("Keterangan", "")
            
            submit_button = st.form_submit_button("Simpan Data")
            
            if submit_button and st.session_state.selected_perusahaan_id:
                try:
                    # Fungsi simpan_realisasi_anggaran sekarang secara otomatis menghitung saldo yang benar
                    new_saldo = simpan_realisasi_anggaran(
                        st.session_state.selected_perusahaan_id,
                        tanggal,
                        debet,
                        kredit,
                        saldo,  # Parameter saldo ini sekarang tidak digunakan, tetapi dikirim untuk kompatibilitas
                        volume,
                        keterangan
                    )
                    st.success(f"Realisasi anggaran berhasil disimpan! Saldo baru: {format_currency(new_saldo)}")
                    st.rerun()
                except Exception as e:
                    st.error(f"Terjadi kesalahan saat menyimpan data: {e}")
    
    # Display existing data in table
    if anggaran_data:
        st.subheader("Data Realisasi Anggaran")
        
        # Sort by date
        sorted_anggaran = sorted(anggaran_data, key=lambda x: x.tanggal)
        
        # Tambahkan data ID untuk keperluan edit dan hapus
        df_anggaran = pd.DataFrame([
            {
                "ID": a.id,
                "No": i+1,
                "Tanggal": a.tanggal,
                "Debet (In)": a.debet,
                "Kredit (Out)": a.kredit,
                "Saldo": a.saldo,
                "Volume": a.volume,
                "Keterangan": a.keterangan
            } for i, a in enumerate(sorted_anggaran)
        ])
        
        # Tampilkan tabel
        st.dataframe(df_anggaran.drop(columns=["ID"]), use_container_width=True)
        
        # Fitur edit dan hapus data
        st.subheader("Edit/Hapus Data Realisasi Anggaran")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Pilih data untuk diedit
            selected_data_id = st.selectbox(
                "Pilih data untuk diedit/hapus", 
                df_anggaran["ID"].tolist(),
                format_func=lambda x: f"No. {df_anggaran[df_anggaran['ID']==x]['No'].values[0]} - {df_anggaran[df_anggaran['ID']==x]['Tanggal'].values[0]} - {df_anggaran[df_anggaran['ID']==x]['Keterangan'].values[0]}"
            )
            
            # Tampilkan tombol hapus jika terotentikasi
            if st.session_state.is_authenticated:
                if st.button("🗑️ Hapus Data", key="delete_button", help="Hapus data realisasi anggaran yang dipilih"):
                    try:
                        hapus_realisasi_anggaran(selected_data_id, st.session_state.selected_perusahaan_id)
                        st.success(f"Data berhasil dihapus!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Terjadi kesalahan saat menghapus data: {e}")
            else:
                st.warning("Silakan login sebagai admin di sidebar untuk menghapus data")
        
        with col2:
            # Ambil data yang dipilih untuk diedit
            if selected_data_id:
                selected_data = get_realisasi_anggaran_by_id(selected_data_id)
                if selected_data:
                    with st.form("edit_realisasi_anggaran_form"):
                        st.subheader(f"Edit Data #{df_anggaran[df_anggaran['ID']==selected_data_id]['No'].values[0]}")
                        
                        edit_tanggal = st.date_input("Tanggal", value=selected_data.tanggal, key="edit_tanggal")
                        edit_debet = st.number_input("Debet (In)", value=selected_data.debet, min_value=0.0, step=100000.0, key="edit_debet")
                        edit_kredit = st.number_input("Kredit (Out)", value=selected_data.kredit, min_value=0.0, step=100000.0, key="edit_kredit")
                        edit_volume = st.text_input("Volume", value=selected_data.volume, key="edit_volume")
                        edit_keterangan = st.text_area("Keterangan", value=selected_data.keterangan, key="edit_keterangan")
                        
                        edit_submit = st.form_submit_button("Update Data")
                        
                        if edit_submit:
                            try:
                                # Hapus data lama
                                hapus_realisasi_anggaran(selected_data_id, st.session_state.selected_perusahaan_id)
                                
                                # Buat data baru dengan nilai yang sudah diedit
                                new_saldo = simpan_realisasi_anggaran(
                                    st.session_state.selected_perusahaan_id,
                                    edit_tanggal,
                                    edit_debet,
                                    edit_kredit,
                                    0,  # Parameter saldo akan dikalkulasi otomatis
                                    edit_volume,
                                    edit_keterangan
                                )
                                
                                st.success(f"Data berhasil diupdate! Saldo baru: {format_currency(new_saldo)}")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Terjadi kesalahan saat mengupdate data: {e}")
        
        # Visualizations
        st.subheader("Visualisasi")
        
        # Create cumulative cash flow chart
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=df_anggaran["Tanggal"],
            y=df_anggaran["Saldo"],
            mode='lines+markers',
            name='Saldo',
            line=dict(color='green', width=3)
        ))
        
        fig.add_trace(go.Bar(
            x=df_anggaran["Tanggal"],
            y=df_anggaran["Debet (In)"],
            name='Debet (In)',
            marker_color='blue'
        ))
        
        fig.add_trace(go.Bar(
            x=df_anggaran["Tanggal"],
            y=-df_anggaran["Kredit (Out)"],
            name='Kredit (Out)',
            marker_color='red'
        ))
        
        fig.update_layout(
            title='Arus Kas dan Saldo',
            xaxis_title='Tanggal',
            yaxis_title='Jumlah (Rp)',
            barmode='relative'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Summary section
        st.subheader("Kesimpulan Realisasi Anggaran")
        
        # Tambahkan tombol untuk memperbaiki saldo jika diperlukan (hanya untuk admin)
        if st.session_state.is_authenticated:
            if st.button("Perbaiki Semua Saldo"):
                try:
                    fix_all_realisasi_anggaran_saldo()
                    st.success("Semua saldo telah diperbaiki. Halaman akan dimuat ulang.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Terjadi kesalahan saat memperbaiki saldo: {e}")
        else:
            st.info("Login sebagai admin untuk mengakses fitur perbaikan saldo")
        
        total_debet = sum(a.debet for a in anggaran_data)
        total_kredit = sum(a.kredit for a in anggaran_data)
        current_saldo = df_anggaran["Saldo"].iloc[-1] if not df_anggaran.empty else 0
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Dana Masuk", format_currency(total_debet))
        
        with col2:
            st.metric("Total Pengeluaran", format_currency(total_kredit))
        
        with col3:
            st.metric("Saldo Akhir", format_currency(current_saldo))
        
        # Grouping kredit by keterangan
        if not df_anggaran.empty:
            # Membuat data frame untuk analisis
            kredit_df = df_anggaran[df_anggaran["Kredit (Out)"] > 0].copy()
            
            if not kredit_df.empty:
                # Tambahkan kolom total volume untuk setiap kategori
                volume_by_category = {}
                for _, row in kredit_df.iterrows():
                    kategori = row["Keterangan"]
                    volume = row["Volume"]
                    if kategori in volume_by_category:
                        volume_by_category[kategori] += f", {volume}"
                    else:
                        volume_by_category[kategori] = volume
                
                # Agregasi berdasarkan kategori
                kredit_by_category = kredit_df.groupby("Keterangan")["Kredit (Out)"].sum().reset_index()
                
                # Tambahkan informasi volume ke hover text
                hover_data = {
                    "Kredit (Out)": True,
                    "Volume": [volume_by_category.get(k, "N/A") for k in kredit_by_category["Keterangan"]]
                }
                
                # Hitung total biaya
                total_kredit = kredit_by_category["Kredit (Out)"].sum()
                
                # Buat pie chart dengan informasi tambahan
                fig_pie = px.pie(
                    kredit_by_category,
                    values="Kredit (Out)",
                    names="Keterangan",
                    title=f"Distribusi Pengeluaran (Total: {format_currency(total_kredit)})",
                    hover_data=hover_data,
                    labels={"Kredit (Out)": "Jumlah Pengeluaran", "Volume": "Volume"}
                )
                
                # Tambahkan informasi persentase dan volume ke dalam teks label pie
                fig_pie.update_traces(
                    hovertemplate="<b>%{label}</b><br>Jumlah: %{value}<br>Persentase: %{percent}<br>Volume: %{customdata[1]}"
                )
                
                st.plotly_chart(fig_pie, use_container_width=True)
                
                # Tambahkan detail tabel untuk volume dan biaya
                st.subheader("Detail Pengeluaran per Kategori")
                
                # Buat dataframe detail dengan volume dan biaya
                detail_df = pd.DataFrame({
                    "Kategori": kredit_by_category["Keterangan"],
                    "Total Biaya": [format_currency(val) for val in kredit_by_category["Kredit (Out)"]],
                    "Persentase": [f"{val/total_kredit*100:.2f}%" for val in kredit_by_category["Kredit (Out)"]],
                    "Volume": [volume_by_category.get(k, "N/A") for k in kredit_by_category["Keterangan"]]
                })
                
                st.dataframe(detail_df, use_container_width=True)
    else:
        st.info("Belum ada data realisasi anggaran. Silakan tambahkan data baru menggunakan form di atas.")

# Download PDF section
st.markdown("---")
st.header("Unduh Laporan PDF")

# Fungsi untuk mengubah byte menjadi link unduh
def get_download_link(pdf_bytes, filename="laporan_penjualan_karet.pdf", text="Unduh Laporan PDF"):
    """
    Generates a download link for a PDF file.
    """
    b64 = base64.b64encode(pdf_bytes).decode()
    href = f'<a href="data:application/pdf;base64,{b64}" download="{filename}">{text}</a>'
    return href

# Tombol untuk mengunduh laporan PDF
if st.button("Buat Laporan PDF"):
    if st.session_state.selected_perusahaan_id:
        with st.spinner("Membuat laporan PDF..."):
            try:
                # Dapatkan data perusahaan
                perusahaan = get_perusahaan_by_id(st.session_state.selected_perusahaan_id)
                perusahaan_data = {
                    "nama": perusahaan.nama,
                    "jenis": perusahaan.jenis
                }
                
                # Dapatkan data penjualan karet
                penjualan_karet_data = []
                for p in get_penjualan_karet(st.session_state.selected_perusahaan_id):
                    penjualan_karet_data.append({
                        "nama_perusahaan": perusahaan.nama,
                        "jarak": p.jarak,
                        "harga_jual": format_currency(p.harga_jual),
                        "susut": f"{p.susut}%",
                        "harga_beli": format_currency(p.harga_beli),
                        "berat_awal": f"{p.berat_awal} kg",
                        "berat_jual": f"{p.berat_jual} kg",
                        "total_harga_jual": format_currency(p.total_harga_jual),
                        "total_harga_beli": format_currency(p.total_harga_beli),
                        "keuntungan_kotor": format_currency(p.keuntungan_kotor),
                        "ongkos_kirim": format_currency(p.ongkos_kirim),
                        "keuntungan_bersih": format_currency(p.keuntungan_bersih),
                        "rekomendasi": p.rekomendasi
                    })
                
                # Dapatkan data strategi risiko
                strategi_risiko_data = []
                for s in get_strategi_risiko(st.session_state.selected_perusahaan_id):
                    strategi_risiko_data.append({
                        "aspek": s.aspek,
                        "risiko": s.risiko,
                        "solusi": s.solusi
                    })
                
                # Dapatkan data realisasi anggaran
                realisasi_anggaran_data = []
                for a in sorted(get_realisasi_anggaran(st.session_state.selected_perusahaan_id), key=lambda x: x.tanggal):
                    realisasi_anggaran_data.append({
                        "tanggal": a.tanggal.strftime("%d/%m/%Y"),
                        "debet": format_currency(a.debet),
                        "kredit": format_currency(a.kredit),
                        "saldo": format_currency(a.saldo),
                        "volume": a.volume,
                        "keterangan": a.keterangan
                    })
                
                # Kesimpulan dari data
                kesimpulan = ""
                if penjualan_karet_data:
                    # Ekstrak nilai keuntungan dengan cara yang lebih aman
                    profits = []
                    max_profit_text = "tidak diketahui"
                    min_profit_text = "tidak diketahui"
                    
                    for p in penjualan_karet_data:
                        profit_str = p["keuntungan_bersih"].replace("Rp", "").replace(" ", "").replace(".", "").replace(",", ".")
                        try:
                            profits.append(float(profit_str))
                        except ValueError:
                            pass
                            
                    if profits:
                        max_profit_text = format_currency(max(profits))
                        min_profit_text = format_currency(min(profits))
                    
                    kesimpulan = f"""
                    Berdasarkan analisis data penjualan karet, berikut adalah beberapa kesimpulan utama:
                    • Profitabilitas tertinggi ditemukan pada penjualan dengan keuntungan bersih {max_profit_text}.
                    • Penjualan dengan jarak terjauh memiliki tingkat susut yang lebih tinggi.
                    • Rekomendasi: Fokus pada penjualan ke perusahaan dengan harga jual tinggi dan jarak yang tidak terlalu jauh untuk mengoptimalkan keuntungan.
                    """
                
                # Data untuk PDF
                pdf_data = {
                    "perusahaan": perusahaan_data,
                    "penjualan_karet": penjualan_karet_data,
                    "strategi_risiko": strategi_risiko_data,
                    "realisasi_anggaran": realisasi_anggaran_data,
                    "kesimpulan": kesimpulan
                }
                
                # Tambahkan debugging
                try:
                    # Buat PDF dengan lebih banyak informasi debug
                    st.write("Memulai pembuatan PDF...")
                    pdf_bytes = generate_pdf_penjualan_karet(pdf_data, report_title)
                    
                    # Buat nama file dengan format yang diminta: Laporan_Keuangan_karet(Date, Time).pdf
                    current_datetime = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"Laporan_Keuangan_karet({current_datetime}).pdf"
                    
                    # Tampilkan link unduh dengan nama file yang sesuai
                    st.markdown(get_download_link(pdf_bytes, filename=filename), unsafe_allow_html=True)
                    st.success("Laporan PDF berhasil dibuat!")
                except Exception as e:
                    import traceback
                    st.error(f"Terjadi kesalahan saat membuat PDF: {e}")
                    st.code(traceback.format_exc())
            except Exception as e:
                st.error(f"Terjadi kesalahan saat membuat laporan PDF: {e}")
    else:
        st.error("Silakan pilih perusahaan terlebih dahulu.")

# Footer
st.markdown("---")
st.markdown("© 2025 Aplikasi Laporan Penjualan Karet")