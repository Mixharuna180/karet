from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import cm
from io import BytesIO
import datetime
from utils import format_currency

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
        pagesize=A4,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
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
            ongkos_data.append([
                p.get('nama_perusahaan', ''),
                p.get('ongkos_kirim', ''),
                p.get('keuntungan_bersih', ''),
                p.get('rekomendasi', '')
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
            strategi_data.append([
                str(i+1),
                s.get('aspek', ''),
                s.get('risiko', ''),
                s.get('solusi', '')
            ])
        
        col_widths = [doc.width * w for w in [0.05, 0.25, 0.3, 0.4]]
        strategi_table = Table(strategi_data, colWidths=col_widths)
        strategi_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 1), (0, -1), 'CENTER')
        ]))
        
        content.append(strategi_table)
        content.append(Spacer(1, 24))
    
    # Realisasi Anggaran
    if 'realisasi_anggaran' in data and data['realisasi_anggaran']:
        content.append(Paragraph("Realisasi Anggaran", header_style))
        
        anggaran_header = ['No', 'Tanggal', 'Debet (In)', 'Kredit (Out)', 'Saldo', 'Volume', 'Keterangan']
        anggaran_data = [anggaran_header]
        
        for i, a in enumerate(data['realisasi_anggaran']):
            anggaran_data.append([
                str(i+1),
                a.get('tanggal', ''),
                a.get('debet', ''),
                a.get('kredit', ''),
                a.get('saldo', ''),
                a.get('volume', ''),
                a.get('keterangan', '')
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