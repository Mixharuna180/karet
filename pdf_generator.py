from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle 
from reportlab.lib import colors
from reportlab.lib.units import cm, inch
from io import BytesIO
import datetime
import textwrap
import matplotlib.pyplot as plt
import numpy as np
import io
import pandas as pd
import matplotlib
matplotlib.use('Agg')
from utils import format_currency

def wrap_text(text, max_width=40, add_spacing=False):
    """
    Wraps text to fit within specified width and optionally adds spacing between paragraphs
    
    Args:
        text (str): Text to wrap
        max_width (int): Maximum width in characters
        add_spacing (bool): Whether to add extra spacing between paragraphs (numbered items)
        
    Returns:
        str: Wrapped text with proper spacing
    """
    if not isinstance(text, str):
        text = str(text)
    
    import re
    
    # Jika format spasi tambahan diminta, kita ubah teks dengan XML markup untuk ReportLab
    if add_spacing:
        # Bersihkan teks dari newline yang mungkin sudah ada
        text = re.sub(r'\s+', ' ', text)
        
        # Deteksi pola item bernomor dan sub-item
        
        # 1. Temukan semua angka diikuti titik (misal: "1.", "2.")
        numbered_items = re.findall(r'(\d+\.\s+[^0-9]+?)(?=\d+\.\s+|$)', text)
        
        # Format khusus untuk ReportLab
        new_text = ""
        
        # Jika ada format penomoran, lakukan formatting khusus
        if numbered_items:
            # Format setiap item bernomor
            for item in numbered_items:
                # Pisahkan nomor dan teks setelahnya
                parts = re.match(r'(\d+\.\s+)(.*)', item)
                if parts:
                    item_num = parts.group(1)
                    item_text = parts.group(2)
                    
                    # Cari sub-item dengan huruf (a., b., dst)
                    sub_items = re.findall(r'([a-z]\.\s+[^a-z\.]+?)(?=[a-z]\.\s+|$)', item_text)
                    
                    if sub_items:
                        # Jika ada sub-item, format dengan paragraf terpisah
                        formatted_sub_items = []
                        for sub_item in sub_items:
                            sub_parts = re.match(r'([a-z]\.\s+)(.*)', sub_item)
                            if sub_parts:
                                sub_num = sub_parts.group(1)
                                sub_text = sub_parts.group(2)
                                formatted_sub_items.append(f"<br/><br/>{sub_num}{sub_text}")
                        
                        # Gabungkan dengan item utama
                        new_text += f"<para>{item_num}{' '.join(formatted_sub_items)}</para><br/>"
                    else:
                        # Jika tidak ada sub-item, tambahkan secara normal
                        new_text += f"<para>{item}</para><br/>"
            
            # Gunakan teks yang sudah diformat
            text = new_text if new_text else text
        
        # Jika tidak ditemukan format penomoran, coba format berdasarkan pola lain
        if not numbered_items:
            # Tambahkan spasi antara paragraf biasa
            text = re.sub(r'(\.\s+)([A-Z])', r'.\n\n\2', text)
    
    # Untuk teks dengan format XML
    if '<para>' in text or '<br/>' in text:
        return text
    
    # Untuk teks biasa, lakukan wrapping seperti biasa
    paragraphs = text.split('\n\n')
    wrapped_paragraphs = []
    
    for p in paragraphs:
        wrapped = textwrap.fill(p, width=max_width)
        wrapped_paragraphs.append(wrapped)
    
    return '\n\n'.join(wrapped_paragraphs)

def parse_currency_id(currency_str):
    """
    Parses Indonesian formatted currency string to float.
    
    Args:
        currency_str (str): Currency string, e.g. 'Rp1.000.000' or '1.000.000'
        
    Returns:
        float: Parsed float value
    """
    if not isinstance(currency_str, str):
        return float(currency_str) if currency_str is not None else 0.0
    
    # Remove Rp, spaces, and convert Indonesian number format to international format
    value_str = currency_str.replace('Rp', '').replace(' ', '').replace('.', '').replace(',', '.')
    try:
        return float(value_str)
    except ValueError:
        print(f"Tidak dapat mengkonversi nilai: {currency_str}")
        return 0.0

def create_cash_flow_chart(anggaran_data):
    """
    Create a cash flow chart for PDF report
    
    Args:
        anggaran_data (list): List of dictionaries with realisasi anggaran data
        
    Returns:
        Image: ReportLab Image object
    """
    # Convert data to right format
    dates = []
    debets = []
    kredits = []
    saldos = []
    
    for item in anggaran_data:
        # Convert date from string to datetime if needed
        if isinstance(item.get('tanggal'), str):
            date_val = datetime.datetime.strptime(item.get('tanggal'), "%d/%m/%Y")
        else:
            date_val = item.get('tanggal')
            
        dates.append(date_val)
        
        # Parse numeric values from currency strings
        debet_val = parse_currency_id(item.get('debet', 0))
        kredit_val = parse_currency_id(item.get('kredit', 0))
        saldo_val = parse_currency_id(item.get('saldo', 0))
        
        debets.append(debet_val)
        kredits.append(kredit_val)
        saldos.append(saldo_val)
    
    # Create figure
    plt.figure(figsize=(10, 5))
    
    # Bar chart for debet and kredit
    bar_width = 0.35
    x = np.arange(len(dates))
    plt.bar(x - bar_width/2, debets, bar_width, label='Debet (In)', color='blue')
    plt.bar(x + bar_width/2, [-k for k in kredits], bar_width, label='Kredit (Out)', color='red')
    
    # Line chart for saldo
    plt.plot(x, saldos, 'go-', linewidth=2, markersize=8, label='Saldo')
    
    # Format the chart
    plt.xlabel('Tanggal')
    plt.ylabel('Rupiah')
    plt.title('Arus Kas dan Saldo')
    plt.xticks(x, [d.strftime('%d/%m/%Y') if isinstance(d, datetime.datetime) else d for d in dates], rotation=45)
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    
    # Save to BytesIO
    img_data = BytesIO()
    plt.savefig(img_data, format='png', dpi=150)
    img_data.seek(0)
    plt.close()
    
    # Return as ReportLab Image
    return Image(img_data, width=700, height=350)

def create_distribution_chart(anggaran_data):
    """
    Create a pie chart showing distribution of kredit (expenses) with volume and total
    
    Args:
        anggaran_data (list): List of dictionaries with realisasi anggaran data
        
    Returns:
        Image: ReportLab Image object
    """
    # Create a DataFrame from the data
    expense_data = {}
    volume_data = {}
    
    for item in anggaran_data:
        keterangan = item.get('keterangan', 'Lainnya')
        
        # Use our parse_currency_id function to safely convert values
        kredit_val = parse_currency_id(item.get('kredit', 0))
        
        if kredit_val > 0:  # Only include expenses
            if keterangan in expense_data:
                expense_data[keterangan] += kredit_val
                volume_data[keterangan] += f", {item.get('volume', '')}"
            else:
                expense_data[keterangan] = kredit_val
                volume_data[keterangan] = item.get('volume', '')
    
    # Create figure
    if expense_data:
        plt.figure(figsize=(8, 6))
        
        # Create pie chart
        labels = list(expense_data.keys())
        sizes = list(expense_data.values())
        
        # Add percentage, value and volume to labels
        total = sum(sizes)
        labels_with_info = [f"{l}\n{s/total*100:.1f}%\n{format_currency(s)}\nVol: {volume_data[l]}" for l, s in zip(labels, sizes)]
        
        plt.pie(sizes, labels=labels_with_info, autopct='', startangle=90, shadow=False, 
                wedgeprops={'edgecolor': 'white', 'linewidth': 1})
        
        plt.axis('equal')
        plt.title(f'Distribusi Pengeluaran (Total: {format_currency(total)})')
        plt.tight_layout()
        
        # Save to BytesIO
        img_data = BytesIO()
        plt.savefig(img_data, format='png', dpi=150)
        img_data.seek(0)
        plt.close()
        
        # Return as ReportLab Image
        return Image(img_data, width=500, height=375)
    
    return None

def create_price_comparison_chart(harga_tertinggi_data, harga_terendah_data):
    """
    Create a chart comparing highest and lowest prices for SICOM x SIR 20
    
    Args:
        harga_tertinggi_data (list): List of dictionaries with highest price data
        harga_terendah_data (list): List of dictionaries with lowest price data
        
    Returns:
        Image: ReportLab Image object
    """
    try:
        # Convert data to right format for plotting
        df_tertinggi = pd.DataFrame([
            {
                "Tanggal": item.get('tanggal'),
                "Harga SIR (Rp)": parse_currency_id(item.get('harga_sir_rupiah', 0)),
                "Tipe": "Tertinggi",
                "Tahun": item.get('tanggal').year if hasattr(item.get('tanggal'), 'year') else 2025
            } for item in harga_tertinggi_data if item.get('tanggal')
        ])
        
        df_terendah = pd.DataFrame([
            {
                "Tanggal": item.get('tanggal'),
                "Harga SIR (Rp)": parse_currency_id(item.get('harga_sir_rupiah', 0)),
                "Tipe": "Terendah",
                "Tahun": item.get('tanggal').year if hasattr(item.get('tanggal'), 'year') else 2025
            } for item in harga_terendah_data if item.get('tanggal')
        ])
        
        # Combine data
        df_combined = pd.concat([df_tertinggi, df_terendah])
        
        if not df_combined.empty:
            plt.figure(figsize=(10, 6))
            
            # Create line chart
            for tipe, group in df_combined.groupby('Tipe'):
                color = 'green' if tipe == 'Tertinggi' else 'red'
                plt.plot(group['Tanggal'], group['Harga SIR (Rp)'], marker='o', linestyle='-', label=tipe, color=color)
            
            plt.title('Perbandingan Harga SIR 20 Tertinggi vs Terendah')
            plt.xlabel('Tanggal')
            plt.ylabel('Harga SIR (Rp)')
            plt.grid(True, linestyle='--', alpha=0.7)
            plt.legend()
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            # Calculate average values for annotation
            avg_tertinggi = df_tertinggi['Harga SIR (Rp)'].mean() if not df_tertinggi.empty else 0
            avg_terendah = df_terendah['Harga SIR (Rp)'].mean() if not df_terendah.empty else 0
            selisih = avg_tertinggi - avg_terendah
            persen_selisih = (selisih / avg_terendah) * 100 if avg_terendah > 0 else 0
            
            # Add annotation box
            textstr = f"Rata-rata Tertinggi: {format_currency(avg_tertinggi)}\n"
            textstr += f"Rata-rata Terendah: {format_currency(avg_terendah)}\n"
            textstr += f"Selisih: {format_currency(selisih)} ({persen_selisih:.1f}%)"
            
            props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
            plt.annotate(textstr, xy=(0.05, 0.95), xycoords='axes fraction', 
                        bbox=props, verticalalignment='top')
            
            # Save to BytesIO
            img_data = BytesIO()
            plt.savefig(img_data, format='png', dpi=150)
            img_data.seek(0)
            plt.close()
            
            # Return as ReportLab Image
            return Image(img_data, width=500, height=300)
            
    except Exception as e:
        print(f"Error creating price comparison chart: {e}")
    
    return None

def generate_pdf_penjualan_karet(data, title="Laporan Penjualan Karet"):
    """
    Generate a PDF report for penjualan karet.
    
    Args:
        data (dict): Dictionary containing all penjualan karet data
        title (str): Title for the report
        
    Returns:
        bytes: PDF file as bytes
    """
    buffer = BytesIO()
    
    # Create PDF document
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),  # Use landscape orientation for wider tables
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    
    # Get styles
    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    subtitle_style = styles['Heading2']
    normal_style = styles['Normal']
    
    # Custom styles
    header_style = ParagraphStyle(
        'HeaderStyle',
        parent=styles['Heading2'],
        textColor=colors.darkblue,
        spaceAfter=12
    )
    
    # Build content
    content = []
    
    # Title
    title_text = Paragraph(title, title_style)
    content.append(title_text)
    content.append(Spacer(1, 12))
    
    # Date
    date_str = datetime.datetime.now().strftime('%d %B %Y')
    date_paragraph = Paragraph(f"Tanggal: {date_str}", normal_style)
    content.append(date_paragraph)
    content.append(Spacer(1, 12))
    
    # Perusahaan information
    if 'perusahaan' in data:
        perusahaan = data['perusahaan']
        perusahaan_info = Paragraph(f"<b>Perusahaan:</b> {perusahaan.get('nama', '')}<br/><b>Jenis:</b> {perusahaan.get('jenis', '')}", normal_style)
        content.append(perusahaan_info)
        content.append(Spacer(1, 24))
    
    # Rencana Penjualan Karet
    if 'penjualan_karet' in data and data['penjualan_karet']:
        content.append(Paragraph("Rencana Penjualan Bokar", header_style))
        
        # Create table data
        penjualan_header = ['Pabrik', 'Jarak (km)', 'Harga Jual (Rp/kg)', 'Susut (%)', 
                           'Harga Beli (Rp/kg)', 'Berat Awal (kg)', 'Berat Jual (kg)', 
                           'Total Harga Jual (Rp)', 'Total Harga Beli (Rp)', 'Keuntungan Kotor (Rp)']
        
        penjualan_data = [penjualan_header]
        
        for p in data['penjualan_karet']:
            penjualan_data.append([
                p.get('nama_perusahaan', ''),
                p.get('jarak', ''),
                p.get('harga_jual', ''),
                p.get('susut', ''),
                p.get('harga_beli', ''),
                p.get('berat_awal', ''),
                p.get('berat_jual', ''),
                p.get('total_harga_jual', ''),
                p.get('total_harga_beli', ''),
                p.get('keuntungan_kotor', '')
            ])
        
        # Create the table
        col_widths = [doc.width * w for w in [0.15, 0.07, 0.09, 0.07, 0.09, 0.08, 0.08, 0.12, 0.12, 0.13]]
        penjualan_table = Table(penjualan_data, colWidths=col_widths)
        penjualan_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (1, 1), (-1, -1), 'RIGHT')
        ]))
        
        content.append(penjualan_table)
        content.append(Spacer(1, 24))
        
        # Ongkos Kirim dan Keuntungan Bersih
        content.append(Paragraph("Detail Keuntungan Bersih", subtitle_style))
        
        # Create table for the second part
        ongkos_header = ['Pabrik', 'Ongkos Kirim (Rp)', 'Keuntungan Bersih (Rp)', 'Rekomendasi']
        ongkos_data = [ongkos_header]
        
        for p in data['penjualan_karet']:
            # Wrap rekomendasi text so it doesn't exceed the column width
            rekomendasi_text = p.get('rekomendasi', '')
            wrapped_rekomendasi = Paragraph(wrap_text(rekomendasi_text, max_width=60), normal_style)
            
            ongkos_data.append([
                p.get('nama_perusahaan', ''),
                p.get('ongkos_kirim', ''),
                p.get('keuntungan_bersih', ''),
                wrapped_rekomendasi
            ])
        
        col_widths = [doc.width * w for w in [0.15, 0.2, 0.2, 0.45]]
        ongkos_table = Table(ongkos_data, colWidths=col_widths)
        ongkos_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (1, 1), (2, -1), 'RIGHT')
        ]))
        
        content.append(ongkos_table)
        content.append(Spacer(1, 24))
    
    # Strategi dan Risiko
    if 'strategi_risiko' in data and data['strategi_risiko']:
        content.append(Paragraph("Strategi dan Risiko Pasar Penjualan Karet", header_style))
        
        strategi_header = ['No', 'Aspek', 'Risiko', 'Solusi']
        strategi_data = [strategi_header]
        
        # Custom style untuk paragraf dengan spasi
        numbered_style = ParagraphStyle(
            'NumberedStyle',
            parent=normal_style,
            firstLineIndent=0,
            leftIndent=0,
            spaceBefore=5,
            spaceAfter=5,
            leading=14  # Meningkatkan spasi antar baris
        )
        
        for i, s in enumerate(data['strategi_risiko']):
            # Format teks aspek secara normal
            aspek_text = Paragraph(wrap_text(s.get('aspek', ''), max_width=30), normal_style)
            
            # Format teks risiko dengan struktur paragraf bernomor
            risiko_raw = s.get('risiko', '')
            risiko_formatted = ""
            
            # Impor modul re untuk regex
            import re
            
            # Coba format berdasarkan struktur yang lebih umum
            # Pertama coba cari apakah ada pola huruf+titik (a., b., etc) yang umum di sub-item
            letter_pattern = re.compile(r'([a-z]\.\s+)([^a-z\.]+?)(?=[a-z]\.\s+|$)')
            letter_items = letter_pattern.findall(risiko_raw)
            
            # Coba cari pola angka+titik (1., 2., etc) juga
            number_pattern = re.compile(r'(\d+\.\s+)([^0-9\.]+?)(?=\d+\.\s+|$)')
            number_items = number_pattern.findall(risiko_raw)
            
            if letter_items:
                # Format khusus untuk sub-item berhuruf
                for mark, item_text in letter_items:
                    risiko_formatted += f"<br/><b>{mark}</b>{item_text}<br/>"
                
                # Bersihkan tag berulang
                risiko_formatted = risiko_formatted.replace("<br/><br/>", "<br/>")
            elif number_items:
                # Format untuk item bernomor - dengan spasi yang jelas
                for mark, item_text in number_items:
                    risiko_formatted += f"<b>{mark}</b>{item_text}<br/><br/>"
                
                # Bersihkan tag berulang
                risiko_formatted = risiko_formatted.replace("<br/><br/><br/>", "<br/><br/>")
            else:
                # Jika tidak ada pola terdeteksi, coba deteksi secara manual
                # Pertama, coba cari pola numerik yang diikuti titik (1., 2., etc)
                parts = re.split(r'((?:^|\s+)\d+\.\s+)', risiko_raw)
                
                if len(parts) > 1:
                    # Ada pola penomoran terdeteksi
                    risiko_formatted = parts[0] if parts[0].strip() else ""  # Teks awal jika ada
                    
                    for idx in range(1, len(parts), 2):
                        if idx+1 < len(parts):
                            # Format nomor dan kontennya dengan spasi yang jelas
                            marker = parts[idx].strip()
                            text = parts[idx+1].strip()
                            
                            # Cek apakah ada sub-poin dengan huruf
                            sub_parts = re.split(r'((?:^|\s+)[a-z]\.\s+)', text)
                            
                            if len(sub_parts) > 1:
                                # Ada sub-poin, format secara khusus
                                risiko_formatted += f"<br/><br/><b>{marker}</b>{sub_parts[0]}"
                                
                                for j in range(1, len(sub_parts), 2):
                                    if j+1 < len(sub_parts):
                                        sub_marker = sub_parts[j].strip()
                                        sub_text = sub_parts[j+1].strip()
                                        risiko_formatted += f"<br/>&nbsp;&nbsp;&nbsp;<b>{sub_marker}</b> {sub_text}"
                                    else:
                                        # Kasus terakhir
                                        risiko_formatted += f"<br/>&nbsp;&nbsp;&nbsp;{sub_parts[j]}"
                            else:
                                # Tidak ada sub-poin, format normal
                                risiko_formatted += f"<br/><br/><b>{marker}</b>{text}"
                        else:
                            # Kasus terakhir
                            risiko_formatted += f"<br/><br/>{parts[idx]}"
                else:
                    # Coba cari pola huruf (a., b., etc)
                    parts = re.split(r'((?:^|\s+)[a-z]\.\s+)', risiko_raw)
                    
                    if len(parts) > 1:
                        # Ada pola huruf terdeteksi
                        risiko_formatted = parts[0] + "<br/>"  # Teks awal
                        
                        for i in range(1, len(parts), 2):
                            if i+1 < len(parts):
                                # Format huruf dan kontennya
                                marker = parts[i].strip()
                                text = parts[i+1].strip()
                                risiko_formatted += f"<br/><b>{marker}</b> {text}<br/>"
                            else:
                                # Kasus terakhir
                                risiko_formatted += f"<br/>{parts[i]}"
                    else:
                        # Tidak ada pola terdeteksi, gunakan teks asli
                        risiko_formatted = risiko_raw
            
            # Format sama untuk teks solusi
            solusi_raw = s.get('solusi', '')
            solusi_formatted = ""
            
            # Coba format berdasarkan struktur yang lebih umum
            # Pertama coba cari apakah ada pola huruf+titik (a., b., etc) yang umum di sub-item
            letter_pattern = re.compile(r'([a-z]\.\s+)([^a-z\.]+?)(?=[a-z]\.\s+|$)')
            letter_items = letter_pattern.findall(solusi_raw)
            
            # Coba cari pola angka+titik (1., 2., etc) juga
            number_pattern = re.compile(r'(\d+\.\s+)([^0-9\.]+?)(?=\d+\.\s+|$)')
            number_items = number_pattern.findall(solusi_raw)
            
            if letter_items:
                # Format khusus untuk sub-item berhuruf
                for mark, item_text in letter_items:
                    solusi_formatted += f"<br/><b>{mark}</b>{item_text}<br/>"
                
                # Bersihkan tag berulang
                solusi_formatted = solusi_formatted.replace("<br/><br/>", "<br/>")
            elif number_items:
                # Format untuk item bernomor
                for mark, item_text in number_items:
                    solusi_formatted += f"<b>{mark}</b>{item_text}<br/><br/>"
                
                # Bersihkan tag berulang
                solusi_formatted = solusi_formatted.replace("<br/><br/><br/>", "<br/><br/>")
            else:
                # Jika tidak ada pola terdeteksi, coba format manual
                # Cari kemungkinan pola a., b. etc dalam teks
                parts = re.split(r'((?:^|\s+)[a-z]\.\s+)', solusi_raw)
                
                if len(parts) > 1:
                    # Ada pola huruf, format secara manual
                    solusi_formatted = parts[0] + "<br/>"  # Teks awal
                    
                    for i in range(1, len(parts), 2):
                        if i+1 < len(parts):
                            # Gabungkan huruf dengan teks yang mengikutinya
                            marker = parts[i].strip()
                            text = parts[i+1].strip()
                            solusi_formatted += f"<br/><b>{marker}</b> {text}<br/>"
                        else:
                            # Kasus terakhir
                            solusi_formatted += f"<br/>{parts[i]}"
                else:
                    # Tidak ada pola berhuruf terdeteksi, gunakan teks asli
                    solusi_formatted = solusi_raw
            
            # Buat paragraf dengan gaya khusus
            risiko_text = Paragraph(risiko_formatted, numbered_style)
            solusi_text = Paragraph(solusi_formatted, numbered_style)
            
            strategi_data.append([
                str(i+1),
                aspek_text,
                risiko_text,
                solusi_text
            ])
        
        col_widths = [doc.width * w for w in [0.05, 0.25, 0.3, 0.4]]
        strategi_table = Table(strategi_data, colWidths=col_widths)
        strategi_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            # Tambahkan padding untuk baris data agar lebih mudah dibaca
            ('TOPPADDING', (0, 1), (-1, -1), 8),  
            ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),
            # Baris garis lebih tipis agar tidak terlalu memenuhi tabel
            ('LINEWIDTH', (0, 0), (-1, -1), 0.5)
        ]))
        
        content.append(strategi_table)
        content.append(Spacer(1, 24))
    
    # Realisasi Anggaran
    if 'realisasi_anggaran' in data and data['realisasi_anggaran']:
        content.append(Paragraph("Realisasi Anggaran", header_style))
        
        anggaran_header = ['No', 'Tanggal', 'Debet (In)', 'Kredit (Out)', 'Saldo', 'Volume', 'Keterangan']
        anggaran_data = [anggaran_header]
        
        for i, a in enumerate(data['realisasi_anggaran']):
            # Wrap keterangan text
            keterangan_text = Paragraph(wrap_text(a.get('keterangan', ''), max_width=40), normal_style)
            
            anggaran_data.append([
                str(i+1),
                a.get('tanggal', ''),
                a.get('debet', ''),
                a.get('kredit', ''),
                a.get('saldo', ''),
                a.get('volume', ''),
                keterangan_text
            ])
        
        col_widths = [doc.width * w for w in [0.05, 0.12, 0.13, 0.13, 0.13, 0.14, 0.3]]
        anggaran_table = Table(anggaran_data, colWidths=col_widths)
        anggaran_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),
            ('ALIGN', (2, 1), (4, -1), 'RIGHT')
        ]))
        
        content.append(anggaran_table)
        content.append(Spacer(1, 24))
        
        # Add cash flow chart to the report
        try:
            content.append(Paragraph("Visualisasi Arus Kas", subtitle_style))
            cash_flow_chart = create_cash_flow_chart(data['realisasi_anggaran'])
            if cash_flow_chart:
                content.append(cash_flow_chart)
            else:
                content.append(Paragraph("(Tidak ada data yang cukup untuk membuat visualisasi arus kas)", normal_style))
            content.append(Spacer(1, 12))
        except Exception as e:
            print(f"Error saat membuat grafik arus kas: {e}")
            content.append(Paragraph("(Terjadi kesalahan saat membuat visualisasi arus kas)", normal_style))
            content.append(Spacer(1, 12))
            
        # Add distribution pie chart to the report
        try:
            content.append(Paragraph("Distribusi Pengeluaran", subtitle_style))
            distribution_chart = create_distribution_chart(data['realisasi_anggaran'])
            if distribution_chart:
                content.append(distribution_chart)
            else:
                content.append(Paragraph("(Tidak ada data pengeluaran yang cukup untuk membuat visualisasi distribusi)", normal_style))
            content.append(Spacer(1, 12))
        except Exception as e:
            print(f"Error saat membuat grafik distribusi: {e}")
            content.append(Paragraph("(Terjadi kesalahan saat membuat visualisasi distribusi pengeluaran)", normal_style))
            content.append(Spacer(1, 12))
    
    # Harga SICOM x SIR 20
    if 'harga_sicom_sir' in data:
        content.append(Paragraph("Harga SICOM x SIR 20", header_style))
        
        # Buat tabel untuk harga tertinggi
        if 'harga_tertinggi' in data['harga_sicom_sir'] and data['harga_sicom_sir']['harga_tertinggi']:
            content.append(Paragraph("Harga Perbandingan Tertinggi", subtitle_style))
            
            tertinggi_header = ['No', 'Tanggal', 'Harga Rupiah', 'Harga Rp/100', 'Harga SIR SGD', 'Harga SIR (Rp)']
            tertinggi_data = [tertinggi_header]
            
            for i, h in enumerate(data['harga_sicom_sir']['harga_tertinggi']):
                tertinggi_data.append([
                    str(i+1),
                    h.get('tanggal', ''),
                    h.get('harga_rupiah', ''),
                    h.get('harga_rupiah_100', ''),
                    h.get('harga_sir_sgd', ''),
                    h.get('harga_sir_rupiah', '')
                ])
            
            col_widths = [doc.width * w for w in [0.05, 0.15, 0.2, 0.2, 0.2, 0.2]]
            tertinggi_table = Table(tertinggi_data, colWidths=col_widths)
            tertinggi_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ALIGN', (2, 1), (-1, -1), 'RIGHT')
            ]))
            
            content.append(tertinggi_table)
            content.append(Spacer(1, 12))
        
        # Buat tabel untuk harga terendah
        if 'harga_terendah' in data['harga_sicom_sir'] and data['harga_sicom_sir']['harga_terendah']:
            content.append(Paragraph("Harga Perbandingan Terendah", subtitle_style))
            
            terendah_header = ['No', 'Tanggal', 'Harga Rupiah', 'Harga Rp/100', 'Harga SIR SGD', 'Harga SIR (Rp)']
            terendah_data = [terendah_header]
            
            for i, h in enumerate(data['harga_sicom_sir']['harga_terendah']):
                terendah_data.append([
                    str(i+1),
                    h.get('tanggal', ''),
                    h.get('harga_rupiah', ''),
                    h.get('harga_rupiah_100', ''),
                    h.get('harga_sir_sgd', ''),
                    h.get('harga_sir_rupiah', '')
                ])
            
            col_widths = [doc.width * w for w in [0.05, 0.15, 0.2, 0.2, 0.2, 0.2]]
            terendah_table = Table(terendah_data, colWidths=col_widths)
            terendah_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ALIGN', (2, 1), (-1, -1), 'RIGHT')
            ]))
            
            content.append(terendah_table)
            content.append(Spacer(1, 12))
        
        # Tambahkan grafik perbandingan jika kedua data tersedia
        if ('harga_tertinggi' in data['harga_sicom_sir'] and data['harga_sicom_sir']['harga_tertinggi'] and
            'harga_terendah' in data['harga_sicom_sir'] and data['harga_sicom_sir']['harga_terendah']):
            # Buat grafik perbandingan
            comparison_chart = create_price_comparison_chart(
                data['harga_sicom_sir']['harga_tertinggi'],
                data['harga_sicom_sir']['harga_terendah']
            )
            
            if comparison_chart:
                content.append(Paragraph("Grafik Perbandingan Harga", subtitle_style))
                content.append(comparison_chart)
                content.append(Spacer(1, 12))
                
                # Tambahkan kesimpulan dengan penanganan error
                try:
                    # Debugging untuk melihat nilai-nilai yang ada
                    print("Nilai harga tertinggi:")
                    for h in data['harga_sicom_sir']['harga_tertinggi']:
                        print(f"  - {h.get('harga_sir_rupiah', 0)}")
                    
                    # Gunakan list comprehension dengan penanganan error untuk setiap item
                    nilai_tertinggi = []
                    for h in data['harga_sicom_sir']['harga_tertinggi']:
                        try:
                            nilai = parse_currency_id(h.get('harga_sir_rupiah', 0))
                            nilai_tertinggi.append(nilai)
                        except Exception as e:
                            print(f"Error parsing harga tertinggi: {e}")
                    
                    nilai_terendah = []
                    for h in data['harga_sicom_sir']['harga_terendah']:
                        try:
                            nilai = parse_currency_id(h.get('harga_sir_rupiah', 0))
                            nilai_terendah.append(nilai)
                        except Exception as e:
                            print(f"Error parsing harga terendah: {e}")
                    
                    avg_tertinggi = sum(nilai_tertinggi) / len(nilai_tertinggi) if nilai_tertinggi else 0
                    avg_terendah = sum(nilai_terendah) / len(nilai_terendah) if nilai_terendah else 0
                except Exception as e:
                    print(f"Error calculating averages: {e}")
                    avg_tertinggi = 0
                    avg_terendah = 0
                selisih = avg_tertinggi - avg_terendah
                persen_selisih = (selisih / avg_terendah) * 100 if avg_terendah > 0 else 0
                
                content.append(Paragraph("Analisis Perbandingan Harga", subtitle_style))
                kesimpulan_text = f"""
                Berdasarkan analisis data harga SICOM x SIR 20, dapat disimpulkan:
                
                1. Selisih rata-rata antara harga tertinggi dan terendah adalah {format_currency(selisih)} atau sekitar {persen_selisih:.2f}%.
                2. Secara historis, terdapat fluktuasi signifikan pada harga SIR 20 yang dapat menjadi pertimbangan dalam strategi jual-beli.
                3. Penting untuk memperhatikan tren harga berdasarkan bulan untuk menentukan waktu optimal dalam transaksi.
                """
                content.append(Paragraph(kesimpulan_text, normal_style))
        
        content.append(Spacer(1, 24))
    
    # Kesimpulan & Rekomendasi
    if 'kesimpulan' in data and data['kesimpulan']:
        content.append(Paragraph("Kesimpulan & Rekomendasi", header_style))
        
        kesimpulan_text = data['kesimpulan']
        content.append(Paragraph(kesimpulan_text, normal_style))
        content.append(Spacer(1, 24))
    
    # Footer
    content.append(Spacer(1, 24))
    footer_text = f"Laporan dibuat pada tanggal {date_str}"
    content.append(Paragraph(footer_text, normal_style))
    
    # Build PDF
    doc.build(content)
    pdf_data = buffer.getvalue()
    buffer.close()
    
    return pdf_data