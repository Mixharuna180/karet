import io
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.graphics.shapes import Drawing, Line
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.piecharts import Pie
from utils import format_currency, format_percentage

def generate_pdf(report_data):
    """
    Generate a PDF report from the financial data.
    
    Args:
        report_data (dict): Dictionary containing all financial data for the report
        
    Returns:
        bytes: PDF file as bytes
    """
    # Create an in-memory PDF
    buffer = io.BytesIO()
    
    # Set up the document
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=letter, 
        rightMargin=72, 
        leftMargin=72, 
        topMargin=72, 
        bottomMargin=72
    )
    
    # Get sample stylesheets
    styles = getSampleStyleSheet()
    
    # Define custom styles
    styles.add(ParagraphStyle(
        name='Title',
        parent=styles['Heading1'],
        fontSize=16,
        alignment=1  # Center alignment
    ))
    
    styles.add(ParagraphStyle(
        name='Subtitle',
        parent=styles['Heading2'],
        fontSize=14,
        alignment=1  # Center alignment
    ))
    
    styles.add(ParagraphStyle(
        name='Section',
        parent=styles['Heading2'],
        fontSize=12,
        spaceAfter=6
    ))
    
    styles.add(ParagraphStyle(
        name='Subsection',
        parent=styles['Heading3'],
        fontSize=10,
        spaceAfter=3
    ))
    
    styles.add(ParagraphStyle(
        name='Normal',
        parent=styles['Normal'],
        fontSize=9,
        spaceAfter=6
    ))
    
    # Initialize the document content
    elements = []
    
    # Add title
    elements.append(Paragraph(report_data['title'], styles['Title']))
    elements.append(Spacer(1, 0.25 * inch))
    
    # Add date information
    period_info = f"Period: {report_data['period_type']} "
    if report_data['period_type'] == "Yearly":
        period_info += str(report_data['selected_year'])
    else:
        period_info += f"{report_data['selected_period']} {report_data['selected_year']}"
    
    elements.append(Paragraph(period_info, styles['Subtitle']))
    elements.append(Spacer(1, 0.5 * inch))
    
    # 1. Financial Summary Section
    elements.append(Paragraph("1. Financial Summary", styles['Section']))
    
    # Calculate summary data
    selected_year = report_data['selected_year']
    total_revenue = sum(report_data['revenue'][selected_year].values())
    total_cogs = sum(report_data['cogs'][selected_year].values())
    total_op_expenses = sum(report_data['op_expenses'][selected_year].values())
    total_other_expenses = sum(report_data['other_expenses'][selected_year].values())
    net_profit = total_revenue - total_cogs - total_op_expenses - total_other_expenses
    
    # Calculate cash flows
    op_cash_flow = sum(report_data['op_cash_flow'][selected_year].values())
    inv_cash_flow = sum(report_data['inv_cash_flow'][selected_year].values())
    fin_cash_flow = sum(report_data['fin_cash_flow'][selected_year].values())
    net_cash_flow = op_cash_flow + inv_cash_flow + fin_cash_flow
    
    # Create summary table
    summary_data = [
        ['Metric', 'Value'],
        ['Annual Revenue', format_currency(total_revenue)],
        ['Net Profit', format_currency(net_profit)],
        ['Net Profit Margin', format_percentage(net_profit / total_revenue if total_revenue > 0 else 0)],
        ['Net Cash Flow', format_currency(net_cash_flow)],
        ['Beginning Balance', format_currency(report_data['current_assets'].get(selected_year, 0))],
        ['Ending Balance', format_currency(report_data['current_assets'].get(selected_year, 0) + net_cash_flow)],
        ['Funding Requirements', format_currency(report_data['funding_requirements'])]
    ]
    
    # Create the table
    summary_table = Table(summary_data, colWidths=[2.5 * inch, 2 * inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (1, 0), colors.black),
        ('ALIGN', (0, 0), (1, 0), 'CENTER'),
        ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(summary_table)
    elements.append(Spacer(1, 0.25 * inch))
    
    # 2. Income Statement Section
    elements.append(Paragraph("2. Income Statement", styles['Section']))
    
    # Prepare income statement data
    if report_data['period_type'] == "Monthly":
        periods = report_data['periods']
    elif report_data['period_type'] == "Quarterly":
        periods = ["Q1", "Q2", "Q3", "Q4"]
    else:  # Yearly
        periods = [str(year) for year in report_data['years']]
    
    # Build income statement table data
    income_statement_data = [['Item'] + periods]
    
    # Revenue row
    revenue_row = ['Revenue']
    cogs_row = ['COGS']
    gross_profit_row = ['Gross Profit']
    op_expenses_row = ['Operating Expenses']
    operating_profit_row = ['Operating Profit']
    other_expenses_row = ['Other Expenses']
    profit_before_tax_row = ['Profit Before Tax']
    tax_row = ['Tax']
    net_profit_row = ['Net Profit']
    
    selected_year = report_data['selected_year']
    
    if report_data['period_type'] == "Monthly":
        for period in periods:
            revenue = report_data['revenue'][selected_year][period]
            cogs = report_data['cogs'][selected_year][period]
            gross_profit = revenue - cogs
            op_expense = report_data['op_expenses'][selected_year][period]
            operating_profit = gross_profit - op_expense
            other_expense = report_data['other_expenses'][selected_year][period]
            profit_before_tax = operating_profit - other_expense
            tax = profit_before_tax * report_data['tax_rate']
            net_profit = profit_before_tax - tax
            
            revenue_row.append(format_currency(revenue))
            cogs_row.append(format_currency(cogs))
            gross_profit_row.append(format_currency(gross_profit))
            op_expenses_row.append(format_currency(op_expense))
            operating_profit_row.append(format_currency(operating_profit))
            other_expenses_row.append(format_currency(other_expense))
            profit_before_tax_row.append(format_currency(profit_before_tax))
            tax_row.append(format_currency(tax))
            net_profit_row.append(format_currency(net_profit))
    elif report_data['period_type'] == "Quarterly":
        # Group months into quarters
        quarters = [
            report_data['periods'][:3],  # Q1
            report_data['periods'][3:6],  # Q2
            report_data['periods'][6:9],  # Q3
            report_data['periods'][9:]   # Q4
        ]
        
        for i, quarter_months in enumerate(quarters):
            q_revenue = sum([report_data['revenue'][selected_year][month] for month in quarter_months])
            q_cogs = sum([report_data['cogs'][selected_year][month] for month in quarter_months])
            q_gross_profit = q_revenue - q_cogs
            q_op_expense = sum([report_data['op_expenses'][selected_year][month] for month in quarter_months])
            q_operating_profit = q_gross_profit - q_op_expense
            q_other_expense = sum([report_data['other_expenses'][selected_year][month] for month in quarter_months])
            q_profit_before_tax = q_operating_profit - q_other_expense
            q_tax = q_profit_before_tax * report_data['tax_rate']
            q_net_profit = q_profit_before_tax - q_tax
            
            revenue_row.append(format_currency(q_revenue))
            cogs_row.append(format_currency(q_cogs))
            gross_profit_row.append(format_currency(q_gross_profit))
            op_expenses_row.append(format_currency(q_op_expense))
            operating_profit_row.append(format_currency(q_operating_profit))
            other_expenses_row.append(format_currency(q_other_expense))
            profit_before_tax_row.append(format_currency(q_profit_before_tax))
            tax_row.append(format_currency(q_tax))
            net_profit_row.append(format_currency(q_net_profit))
    else:  # Yearly
        for year in report_data['years']:
            y_revenue = sum(report_data['revenue'][year].values())
            y_cogs = sum(report_data['cogs'][year].values())
            y_gross_profit = y_revenue - y_cogs
            y_op_expense = sum(report_data['op_expenses'][year].values())
            y_operating_profit = y_gross_profit - y_op_expense
            y_other_expense = sum(report_data['other_expenses'][year].values())
            y_profit_before_tax = y_operating_profit - y_other_expense
            y_tax = y_profit_before_tax * report_data['tax_rate']
            y_net_profit = y_profit_before_tax - y_tax
            
            revenue_row.append(format_currency(y_revenue))
            cogs_row.append(format_currency(y_cogs))
            gross_profit_row.append(format_currency(y_gross_profit))
            op_expenses_row.append(format_currency(y_op_expense))
            operating_profit_row.append(format_currency(y_operating_profit))
            other_expenses_row.append(format_currency(y_other_expense))
            profit_before_tax_row.append(format_currency(y_profit_before_tax))
            tax_row.append(format_currency(y_tax))
            net_profit_row.append(format_currency(y_net_profit))
    
    # Build complete income statement table
    income_statement_data.extend([
        revenue_row,
        cogs_row,
        gross_profit_row,
        op_expenses_row,
        operating_profit_row,
        other_expenses_row,
        profit_before_tax_row,
        tax_row,
        net_profit_row
    ])
    
    # Create the table
    col_widths = [1.5 * inch] + [1 * inch] * len(periods)
    income_table = Table(income_statement_data, colWidths=col_widths)
    
    # Style the table
    income_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        # Highlight Gross Profit, Operating Profit and Net Profit rows
        ('BACKGROUND', (0, 3), (-1, 3), colors.lightgrey),
        ('BACKGROUND', (0, 5), (-1, 5), colors.lightgrey),
        ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey)
    ]))
    
    elements.append(income_table)
    elements.append(Spacer(1, 0.25 * inch))
    
    # Add balance sheet to a new page
    elements.append(PageBreak())
    
    # 3. Balance Sheet Section
    elements.append(Paragraph("3. Balance Sheet", styles['Section']))
    
    # Calculate balance sheet values
    total_assets = report_data['current_assets'][selected_year] + report_data['fixed_assets'][selected_year]
    total_liabilities = report_data['short_term_liabilities'][selected_year] + report_data['long_term_liabilities'][selected_year]
    total_equity = report_data['owner_equity'][selected_year] + report_data['retained_earnings'][selected_year]
    
    # Create balance sheet table
    balance_sheet_data = [
        ['Category', 'Amount'],
        ['Assets', ''],
        ['  Current Assets', format_currency(report_data['current_assets'][selected_year])],
        ['  Fixed Assets', format_currency(report_data['fixed_assets'][selected_year])],
        ['Total Assets', format_currency(total_assets)],
        ['Liabilities', ''],
        ['  Short-term Liabilities', format_currency(report_data['short_term_liabilities'][selected_year])],
        ['  Long-term Liabilities', format_currency(report_data['long_term_liabilities'][selected_year])],
        ['Total Liabilities', format_currency(total_liabilities)],
        ['Equity', ''],
        ["  Owner's Equity", format_currency(report_data['owner_equity'][selected_year])],
        ['  Retained Earnings', format_currency(report_data['retained_earnings'][selected_year])],
        ['Total Equity', format_currency(total_equity)],
        ['Total Liabilities & Equity', format_currency(total_liabilities + total_equity)]
    ]
    
    # Create the table
    balance_sheet_table = Table(balance_sheet_data, colWidths=[3 * inch, 1.5 * inch])
    
    # Style the table
    balance_sheet_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (1, 0), colors.black),
        ('ALIGN', (0, 0), (1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
        ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
        # Make category headers bold
        ('FONTNAME', (0, 1), (0, 1), 'Helvetica-Bold'),
        ('FONTNAME', (0, 5), (0, 5), 'Helvetica-Bold'),
        ('FONTNAME', (0, 9), (0, 9), 'Helvetica-Bold'),
        # Highlight total rows
        ('FONTNAME', (0, 4), (0, 4), 'Helvetica-Bold'),
        ('BACKGROUND', (0, 4), (1, 4), colors.lightgrey),
        ('FONTNAME', (0, 8), (0, 8), 'Helvetica-Bold'),
        ('BACKGROUND', (0, 8), (1, 8), colors.lightgrey),
        ('FONTNAME', (0, 12), (0, 12), 'Helvetica-Bold'),
        ('BACKGROUND', (0, 12), (1, 12), colors.lightgrey),
        ('FONTNAME', (0, 13), (0, 13), 'Helvetica-Bold'),
        ('BACKGROUND', (0, 13), (1, 13), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(balance_sheet_table)
    elements.append(Spacer(1, 0.25 * inch))
    
    # 4. Cash Flow Statement
    elements.append(Paragraph("4. Cash Flow Statement", styles['Section']))
    
    # Prepare cash flow statement data
    cash_flow_data = [['Cash Flow Category'] + periods]
    
    op_cash_row = ['Operational Cash Flow']
    inv_cash_row = ['Investment Cash Flow']
    fin_cash_row = ['Financing Cash Flow']
    net_cash_row = ['Net Cash Flow']
    
    if report_data['period_type'] == "Monthly":
        for period in periods:
            op_cash = report_data['op_cash_flow'][selected_year][period]
            inv_cash = report_data['inv_cash_flow'][selected_year][period]
            fin_cash = report_data['fin_cash_flow'][selected_year][period]
            net_cash = op_cash + inv_cash + fin_cash
            
            op_cash_row.append(format_currency(op_cash))
            inv_cash_row.append(format_currency(inv_cash))
            fin_cash_row.append(format_currency(fin_cash))
            net_cash_row.append(format_currency(net_cash))
    elif report_data['period_type'] == "Quarterly":
        # Group months into quarters
        quarters = [
            report_data['periods'][:3],  # Q1
            report_data['periods'][3:6],  # Q2
            report_data['periods'][6:9],  # Q3
            report_data['periods'][9:]   # Q4
        ]
        
        for quarter_months in quarters:
            q_op_cash = sum([report_data['op_cash_flow'][selected_year][month] for month in quarter_months])
            q_inv_cash = sum([report_data['inv_cash_flow'][selected_year][month] for month in quarter_months])
            q_fin_cash = sum([report_data['fin_cash_flow'][selected_year][month] for month in quarter_months])
            q_net_cash = q_op_cash + q_inv_cash + q_fin_cash
            
            op_cash_row.append(format_currency(q_op_cash))
            inv_cash_row.append(format_currency(q_inv_cash))
            fin_cash_row.append(format_currency(q_fin_cash))
            net_cash_row.append(format_currency(q_net_cash))
    else:  # Yearly
        for year in report_data['years']:
            y_op_cash = sum(report_data['op_cash_flow'][year].values())
            y_inv_cash = sum(report_data['inv_cash_flow'][year].values())
            y_fin_cash = sum(report_data['fin_cash_flow'][year].values())
            y_net_cash = y_op_cash + y_inv_cash + y_fin_cash
            
            op_cash_row.append(format_currency(y_op_cash))
            inv_cash_row.append(format_currency(y_inv_cash))
            fin_cash_row.append(format_currency(y_fin_cash))
            net_cash_row.append(format_currency(y_net_cash))
    
    # Build complete cash flow table
    cash_flow_data.extend([
        op_cash_row,
        inv_cash_row,
        fin_cash_row,
        net_cash_row
    ])
    
    # Create the table
    col_widths = [1.5 * inch] + [1 * inch] * len(periods)
    cash_flow_table = Table(cash_flow_data, colWidths=col_widths)
    
    # Style the table
    cash_flow_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        # Highlight Net Cash Flow row
        ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey)
    ]))
    
    elements.append(cash_flow_table)
    elements.append(Spacer(1, 0.25 * inch))
    
    # Add a page break before projections
    elements.append(PageBreak())
    
    # 5. Financial Projections
    elements.append(Paragraph("5. Financial Projections", styles['Section']))
    
    # Basic projection information
    current_year = selected_year
    projection_text = [
        f"Projection Base Year: {current_year}",
        f"Revenue Growth Rate: {format_percentage(report_data.get('revenue_growth', 0.1))}",
        f"Expense Growth Rate: {format_percentage(report_data.get('expense_growth', 0.08))}"
    ]
    
    for text in projection_text:
        elements.append(Paragraph(text, styles['Normal']))
    
    elements.append(Spacer(1, 0.1 * inch))
    
    # Calculate projections
    current_year_revenue = sum(report_data['revenue'][current_year].values())
    current_year_expenses = (sum(report_data['cogs'][current_year].values()) + 
                           sum(report_data['op_expenses'][current_year].values()) + 
                           sum(report_data['other_expenses'][current_year].values()))
    
    projection_years = 3  # Default to 3 years
    if 'projection_years' in report_data:
        projection_years = report_data['projection_years']
    
    projection_periods = [current_year + i for i in range(projection_years + 1)]  # Include current year
    projected_revenue = [current_year_revenue]
    projected_expenses = [current_year_expenses]
    
    for i in range(1, projection_years + 1):
        proj_rev = current_year_revenue * (1 + report_data.get('revenue_growth', 0.1)) ** i
        proj_exp = current_year_expenses * (1 + report_data.get('expense_growth', 0.08)) ** i
        projected_revenue.append(proj_rev)
        projected_expenses.append(proj_exp)
    
    projected_profit = [r - e for r, e in zip(projected_revenue, projected_expenses)]
    
    # Create projection table
    projection_data = [
        ['Year', 'Revenue', 'Expenses', 'Net Profit', 'Profit Margin'],
    ]
    
    for i, year in enumerate(projection_periods):
        profit_margin = projected_profit[i] / projected_revenue[i] if projected_revenue[i] > 0 else 0
        projection_data.append([
            str(year),
            format_currency(projected_revenue[i]),
            format_currency(projected_expenses[i]),
            format_currency(projected_profit[i]),
            format_percentage(profit_margin)
        ])
    
    # Create the table
    projection_table = Table(projection_data, colWidths=[0.8 * inch, 1.5 * inch, 1.5 * inch, 1.5 * inch, 1 * inch])
    
    # Style the table
    projection_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        # Highlight the base year
        ('BACKGROUND', (0, 1), (-1, 1), colors.lightskyblue)
    ]))
    
    elements.append(projection_table)
    elements.append(Spacer(1, 0.25 * inch))
    
    # 6. KPIs & Financial Ratios
    elements.append(Paragraph("6. KPIs & Financial Ratios", styles['Section']))
    
    # Calculate ratios
    gross_margin = (total_revenue - total_cogs) / total_revenue if total_revenue > 0 else 0
    net_profit_margin = net_profit / total_revenue if total_revenue > 0 else 0
    current_ratio = report_data['current_assets'][selected_year] / report_data['short_term_liabilities'][selected_year] if report_data['short_term_liabilities'][selected_year] > 0 else 0
    debt_equity_ratio = total_liabilities / total_equity if total_equity > 0 else 0
    
    # Create KPIs table
    kpi_data = [
        ['Key Performance Indicator', 'Value'],
        ['Gross Margin', format_percentage(gross_margin)],
        ['Net Profit Margin', format_percentage(net_profit_margin)],
        ['Current Ratio', f"{current_ratio:.2f}"],
        ['Debt-to-Equity Ratio', f"{debt_equity_ratio:.2f}"],
        ['Customer Acquisition Cost (CAC)', format_currency(report_data['cac'][selected_year])],
        ['Lifetime Value (LTV)', format_currency(report_data['ltv'][selected_year])],
        ['LTV:CAC Ratio', f"{report_data['ltv'][selected_year] / report_data['cac'][selected_year]:.2f}" if report_data['cac'][selected_year] > 0 else "N/A"],
        ['Burn Rate', format_currency(report_data['burn_rate'][selected_year])]
    ]
    
    # Create the table
    kpi_table = Table(kpi_data, colWidths=[3 * inch, 1.5 * inch])
    
    # Style the table
    kpi_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (1, 0), colors.black),
        ('ALIGN', (0, 0), (1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
        ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(kpi_table)
    elements.append(Spacer(1, 0.25 * inch))
    
    # Add a page break before financial notes
    elements.append(PageBreak())
    
    # 7. Financial Notes
    elements.append(Paragraph("7. Financial Notes & Funding Information", styles['Section']))
    
    # Growth Strategy
    elements.append(Paragraph("Growth Strategy", styles['Subsection']))
    if report_data['growth_strategy']:
        elements.append(Paragraph(report_data['growth_strategy'], styles['Normal']))
    else:
        elements.append(Paragraph("No growth strategy information provided.", styles['Normal']))
    
    elements.append(Spacer(1, 0.15 * inch))
    
    # Business Risks & Mitigation
    elements.append(Paragraph("Business Risks & Mitigation", styles['Subsection']))
    if report_data['business_risks']:
        elements.append(Paragraph(report_data['business_risks'], styles['Normal']))
    else:
        elements.append(Paragraph("No business risk information provided.", styles['Normal']))
    
    elements.append(Spacer(1, 0.15 * inch))
    
    # Explanation of Variations
    elements.append(Paragraph("Explanation of Significant Variations", styles['Subsection']))
    if report_data['anomalies']:
        elements.append(Paragraph(report_data['anomalies'], styles['Normal']))
    else:
        elements.append(Paragraph("No information about significant variations provided.", styles['Normal']))
    
    elements.append(Spacer(1, 0.15 * inch))
    
    # Funding Information
    elements.append(Paragraph("Funding Requirements & Allocation", styles['Subsection']))
    elements.append(Paragraph(f"Total Funding Required: {format_currency(report_data['funding_requirements'])}", styles['Normal']))
    
    if report_data['funding_allocation']:
        elements.append(Paragraph("Use of Funds:", styles['Normal']))
        elements.append(Paragraph(report_data['funding_allocation'], styles['Normal']))
    else:
        elements.append(Paragraph("No funding allocation information provided.", styles['Normal']))
    
    # Build the PDF
    doc.build(elements)
    
    # Get the value of the BytesIO buffer
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    return pdf_bytes
