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
    get_penjualan_karet, simpan_penjualan_karet,
    get_strategi_risiko, simpan_strategi_risiko,
    get_realisasi_anggaran, simpan_realisasi_anggaran
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

# Sidebar for company selection and data input
with st.sidebar:
    st.header("Konfigurasi Laporan")
    
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
        
        st.dataframe(df_penjualan, use_container_width=True)
        
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
        fig2 = px.scatter(
            df_penjualan,
            x="Jarak (km)",
            y="Harga Jual (Rp/kg)",
            size="Keuntungan Bersih",
            color="Keuntungan Bersih",
            hover_name="Tanggal",
            title="Hubungan antara Jarak, Harga Jual, dan Keuntungan",
        )
        st.plotly_chart(fig2, use_container_width=True)
        
        # Plot susut vs distance
        fig3 = px.scatter(
            df_penjualan,
            x="Jarak (km)",
            y="Susut (%)",
            size="Berat Awal (kg)",
            color="Keuntungan Bersih",
            hover_name="Tanggal",
            title="Hubungan antara Jarak dan Susut",
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
        with st.form("realisasi_anggaran_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                tanggal = st.date_input("Tanggal", date.today(), key="anggaran_tanggal")
                debet = st.number_input("Debet (In)", min_value=0.0, step=100000.0)
                kredit = st.number_input("Kredit (Out)", min_value=0.0, step=100000.0)
            
            with col2:
                # Hitung saldo terakhir
                last_saldo = 0
                if anggaran_data:
                    sorted_data = sorted(anggaran_data, key=lambda x: x.tanggal, reverse=True)
                    last_saldo = sorted_data[0].saldo
                
                # Calculate new saldo
                saldo = last_saldo + debet - kredit
                st.metric("Saldo", format_currency(saldo))
                
                volume = st.text_input("Volume", "")
                keterangan = st.text_area("Keterangan", "")
            
            submit_button = st.form_submit_button("Simpan Data")
            
            if submit_button and st.session_state.selected_perusahaan_id:
                try:
                    simpan_realisasi_anggaran(
                        st.session_state.selected_perusahaan_id,
                        tanggal,
                        debet,
                        kredit,
                        saldo,
                        volume,
                        keterangan
                    )
                    st.success("Realisasi anggaran berhasil disimpan!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Terjadi kesalahan saat menyimpan data: {e}")
    
    # Display existing data in table
    if anggaran_data:
        st.subheader("Data Realisasi Anggaran")
        
        # Sort by date
        sorted_anggaran = sorted(anggaran_data, key=lambda x: x.tanggal)
        
        df_anggaran = pd.DataFrame([
            {
                "No": i+1,
                "Tanggal": a.tanggal,
                "Debet (In)": a.debet,
                "Kredit (Out)": a.kredit,
                "Saldo": a.saldo,
                "Volume": a.volume,
                "Keterangan": a.keterangan
            } for i, a in enumerate(sorted_anggaran)
        ])
        
        st.dataframe(df_anggaran, use_container_width=True)
        
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
            kredit_by_category = df_anggaran[df_anggaran["Kredit (Out)"] > 0].groupby("Keterangan")["Kredit (Out)"].sum().reset_index()
            
            if not kredit_by_category.empty:
                fig_pie = px.pie(
                    kredit_by_category,
                    values="Kredit (Out)",
                    names="Keterangan",
                    title="Distribusi Pengeluaran berdasarkan Kategori"
                )
                st.plotly_chart(fig_pie, use_container_width=True)
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
                    max_profit = max(p["keuntungan_bersih"].replace("Rp", "").replace(".", "").replace(",", ".") for p in penjualan_karet_data)
                    min_profit = min(p["keuntungan_bersih"].replace("Rp", "").replace(".", "").replace(",", ".") for p in penjualan_karet_data)
                    kesimpulan = f"""
                    Berdasarkan analisis data penjualan karet, berikut adalah beberapa kesimpulan utama:
                    • Profitabilitas tertinggi ditemukan pada penjualan dengan keuntungan bersih {max_profit}.
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
                
                # Buat PDF
                pdf_bytes = generate_pdf_penjualan_karet(pdf_data, report_title)
                
                # Tampilkan link unduh
                st.markdown(get_download_link(pdf_bytes), unsafe_allow_html=True)
                st.success("Laporan PDF berhasil dibuat!")
            except Exception as e:
                st.error(f"Terjadi kesalahan saat membuat laporan PDF: {e}")
    else:
        st.error("Silakan pilih perusahaan terlebih dahulu.")

# Footer
st.markdown("---")
st.markdown("© 2025 Aplikasi Laporan Penjualan Karet")