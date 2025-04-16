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
    
    if add_spacing:
        # Mencari pola angka diikuti titik di awal teks (contoh: "1. ", "2. ")
        import re
        # Tambahkan spasi extra sebelum item bernomor (kecuali yang pertama)
        text = re.sub(r'(?<!^)(\d+\.\s)', r'\n\n\1', text)
        
        # Untuk sub-paragraf, tambahkan spasi setelah titik atau koma
        text = re.sub(r'(\.\s|\,\s)(?=[A-Z])', r'\1\n', text)
    
    # Use textwrap to wrap text to fit column width
    paragraphs = text.split('\n\n')
    wrapped_paragraphs = []
    
    for p in paragraphs:
        lines = p.split('\n')
        wrapped_lines = []
        
        for line in lines:
            wrapped_lines.append('\n'.join(textwrap.wrap(line, width=max_width)))
            
        wrapped_paragraphs.append('\n'.join(wrapped_lines))
    
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
        
        for i, s in enumerate(data['strategi_risiko']):
            # Wrap the text in each column with added spacing for better readability
            aspek_text = Paragraph(wrap_text(s.get('aspek', ''), max_width=30), normal_style)
            # Tambahkan spasi khusus untuk kolom risiko karena sering berisi numbering dan sub-paragraf
            risiko_text = Paragraph(wrap_text(s.get('risiko', ''), max_width=35, add_spacing=True), normal_style)
            # Tambahkan spasi khusus untuk kolom solusi juga
            solusi_text = Paragraph(wrap_text(s.get('solusi', ''), max_width=50, add_spacing=True), normal_style)
            
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