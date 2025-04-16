import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import numpy as np
from utils import format_currency, format_percentage
from financial_utils import (
    calculate_net_profit_margin, 
    calculate_gross_margin,
    calculate_current_ratio,
    calculate_debt_to_equity
)
from pdf_generator import generate_pdf
from database import (
    get_companies, get_company_by_id, create_company,
    get_financial_data, save_financial_data,
    get_balance_sheet, save_balance_sheet, 
    get_cash_flow, save_cash_flow,
    get_kpis, save_kpi,
    get_financial_notes, save_financial_note
)

# Set page configuration
st.set_page_config(
    page_title="Aplikasi Laporan Keuangan",
    page_icon="💼",
    layout="wide"
)

# Application title
st.title("Aplikasi Laporan Keuangan untuk Investor")
st.markdown("---")

# Initialize session state variables if they don't exist
if 'periods' not in st.session_state:
    st.session_state.periods = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    st.session_state.years = [datetime.now().year - i for i in range(3)]
    
    # Dapatkan daftar perusahaan dari database
    companies = get_companies()
    if companies:
        # Pilih perusahaan pertama secara default
        st.session_state.selected_company_id = companies[0].id
        st.session_state.selected_company_name = companies[0].name
    else:
        st.session_state.selected_company_id = None
        st.session_state.selected_company_name = ""
    
    # Initialize with empty data
    st.session_state.revenue = {year: {month: 0 for month in st.session_state.periods} for year in st.session_state.years}
    st.session_state.cogs = {year: {month: 0 for month in st.session_state.periods} for year in st.session_state.years}
    st.session_state.op_expenses = {year: {month: 0 for month in st.session_state.periods} for year in st.session_state.years}
    st.session_state.other_expenses = {year: {month: 0 for month in st.session_state.periods} for year in st.session_state.years}
    st.session_state.tax_rate = 0.2
    
    # Balance Sheet
    st.session_state.current_assets = {year: 0 for year in st.session_state.years}
    st.session_state.fixed_assets = {year: 0 for year in st.session_state.years}
    st.session_state.short_term_liabilities = {year: 0 for year in st.session_state.years}
    st.session_state.long_term_liabilities = {year: 0 for year in st.session_state.years}
    st.session_state.owner_equity = {year: 0 for year in st.session_state.years}
    st.session_state.retained_earnings = {year: 0 for year in st.session_state.years}
    
    # Cash Flow
    st.session_state.op_cash_flow = {year: {month: 0 for month in st.session_state.periods} for year in st.session_state.years}
    st.session_state.inv_cash_flow = {year: {month: 0 for month in st.session_state.periods} for year in st.session_state.years}
    st.session_state.fin_cash_flow = {year: {month: 0 for month in st.session_state.periods} for year in st.session_state.years}
    
    # KPIs
    st.session_state.cac = {year: 0 for year in st.session_state.years}
    st.session_state.ltv = {year: 0 for year in st.session_state.years}
    st.session_state.burn_rate = {year: 0 for year in st.session_state.years}
    
    # Projections
    st.session_state.revenue_growth = 0.1
    st.session_state.expense_growth = 0.08
    st.session_state.projection_years = 3
    
    # Financial Notes
    st.session_state.growth_strategy = ""
    st.session_state.business_risks = ""
    st.session_state.anomalies = ""
    st.session_state.funding_requirements = 0
    st.session_state.funding_allocation = ""
    
    # Load data from database if company is selected
    if st.session_state.selected_company_id:
        # Load financial data
        for year in st.session_state.years:
            financial_data = get_financial_data(st.session_state.selected_company_id, year)
            for data in financial_data:
                month = st.session_state.periods[data.month - 1]  # Convert month number to name
                st.session_state.revenue[year][month] = data.revenue
                st.session_state.cogs[year][month] = data.cogs
                st.session_state.op_expenses[year][month] = data.operational_expenses
                st.session_state.other_expenses[year][month] = data.other_expenses
                st.session_state.tax_rate = data.tax_rate
        
        # Load balance sheet data
        for year in st.session_state.years:
            balance_sheets = get_balance_sheet(st.session_state.selected_company_id, year)
            if balance_sheets:
                balance_sheet = balance_sheets[0]  # Get the first one for the year
                st.session_state.current_assets[year] = balance_sheet.current_assets
                st.session_state.fixed_assets[year] = balance_sheet.fixed_assets
                st.session_state.short_term_liabilities[year] = balance_sheet.short_term_liabilities
                st.session_state.long_term_liabilities[year] = balance_sheet.long_term_liabilities
                st.session_state.owner_equity[year] = balance_sheet.owner_equity
                st.session_state.retained_earnings[year] = balance_sheet.retained_earnings
        
        # Load cash flow data
        for year in st.session_state.years:
            cash_flows = get_cash_flow(st.session_state.selected_company_id, year)
            for data in cash_flows:
                month = st.session_state.periods[data.month - 1]  # Convert month number to name
                st.session_state.op_cash_flow[year][month] = data.operational_cash_flow
                st.session_state.inv_cash_flow[year][month] = data.investment_cash_flow
                st.session_state.fin_cash_flow[year][month] = data.financing_cash_flow
        
        # Load KPI data
        for year in st.session_state.years:
            kpis = get_kpis(st.session_state.selected_company_id, year)
            if kpis:
                kpi = kpis[0]  # Get the first one for the year
                st.session_state.cac[year] = kpi.cac
                st.session_state.ltv[year] = kpi.ltv
                st.session_state.burn_rate[year] = kpi.burn_rate
                st.session_state.revenue_growth = kpi.revenue_growth
                st.session_state.expense_growth = kpi.expense_growth
                st.session_state.projection_years = kpi.projection_years
        
        # Load financial notes
        for year in st.session_state.years:
            notes = get_financial_notes(st.session_state.selected_company_id, year)
            if notes and year == st.session_state.years[0]:  # Use only current year notes
                note = notes[0]
                st.session_state.growth_strategy = note.growth_strategy or ""
                st.session_state.business_risks = note.business_risks or ""
                st.session_state.anomalies = note.anomalies or ""
                st.session_state.funding_requirements = note.funding_requirements or 0
                st.session_state.funding_allocation = note.funding_allocation or ""

# Sidebar for report configuration
with st.sidebar:
    st.header("Konfigurasi Laporan")
    
    # Perusahaan Selection
    st.subheader("Pilih Perusahaan")
    
    # Dapatkan daftar perusahaan dari database
    companies = get_companies()
    company_names = [company.name for company in companies]
    company_ids = [company.id for company in companies]
    
    # Tambahkan opsi untuk membuat perusahaan baru
    company_names.append("+ Tambah Perusahaan Baru")
    
    selected_company_index = st.selectbox(
        "Perusahaan", 
        range(len(company_names)), 
        format_func=lambda x: company_names[x]
    )
    
    # Jika user memilih untuk menambah perusahaan baru
    if selected_company_index == len(company_names) - 1:
        with st.form("new_company_form"):
            new_company_name = st.text_input("Nama Perusahaan")
            new_company_industry = st.text_input("Industri")
            new_company_founded = st.date_input("Tanggal Didirikan")
            
            submit_button = st.form_submit_button("Tambah Perusahaan")
            
            if submit_button and new_company_name:
                new_company_id = create_company(new_company_name, new_company_industry, new_company_founded)
                st.session_state.selected_company_id = new_company_id
                st.session_state.selected_company_name = new_company_name
                st.success(f"Perusahaan {new_company_name} berhasil dibuat!")
                st.rerun()
    else:
        # Jika ada perusahaan, update selected_company_id di session_state
        if companies:
            st.session_state.selected_company_id = company_ids[selected_company_index]
            st.session_state.selected_company_name = company_names[selected_company_index]
    
    # Judul Laporan
    report_title = st.text_input("Judul Laporan", f"Laporan Keuangan - {st.session_state.selected_company_name}")
    
    # Pilih Periode
    st.subheader("Pilih Periode")
    period_type = st.selectbox("Jenis Periode", ["Bulanan", "Triwulanan", "Tahunan"])
    selected_year = st.selectbox("Pilih Tahun", st.session_state.years)
    
    # Get current year index for default selection
    current_year_index = st.session_state.years.index(selected_year)
    
    if period_type == "Bulanan":
        periods = st.session_state.periods
    elif period_type == "Triwulanan":
        periods = ["Q1", "Q2", "Q3", "Q4"]
    else:  # Yearly
        periods = [str(year) for year in st.session_state.years]
    
    selected_period = st.selectbox("Pilih Periode", periods)
    
    # Tombol Simpan Data ke Database
    if st.button("Simpan Data ke Database"):
        if st.session_state.selected_company_id:
            # Simpan data finansial untuk setiap bulan/tahun
            for year in st.session_state.years:
                for i, month in enumerate(st.session_state.periods):
                    save_financial_data(
                        st.session_state.selected_company_id,
                        year,
                        i + 1,  # Konversi nama bulan ke angka
                        st.session_state.revenue[year][month],
                        st.session_state.cogs[year][month],
                        st.session_state.op_expenses[year][month],
                        st.session_state.other_expenses[year][month],
                        st.session_state.tax_rate
                    )
                
                # Simpan balance sheet untuk setiap tahun
                save_balance_sheet(
                    st.session_state.selected_company_id,
                    year,
                    st.session_state.current_assets[year],
                    st.session_state.fixed_assets[year],
                    st.session_state.short_term_liabilities[year],
                    st.session_state.long_term_liabilities[year],
                    st.session_state.owner_equity[year],
                    st.session_state.retained_earnings[year]
                )
                
                # Simpan cash flow untuk setiap bulan/tahun
                for i, month in enumerate(st.session_state.periods):
                    save_cash_flow(
                        st.session_state.selected_company_id,
                        year,
                        i + 1,  # Konversi nama bulan ke angka
                        st.session_state.op_cash_flow[year][month],
                        st.session_state.inv_cash_flow[year][month],
                        st.session_state.fin_cash_flow[year][month]
                    )
                
                # Simpan KPI untuk setiap tahun
                save_kpi(
                    st.session_state.selected_company_id,
                    year,
                    st.session_state.cac[year],
                    st.session_state.ltv[year],
                    st.session_state.burn_rate[year],
                    st.session_state.revenue_growth,
                    st.session_state.expense_growth,
                    st.session_state.projection_years
                )
            
            # Simpan financial notes untuk tahun saat ini
            current_year = st.session_state.years[0]
            save_financial_note(
                st.session_state.selected_company_id,
                current_year,
                st.session_state.growth_strategy,
                st.session_state.business_risks,
                st.session_state.anomalies,
                st.session_state.funding_requirements,
                st.session_state.funding_allocation
            )
            
            st.success("Data berhasil disimpan ke database!")
        else:
            st.error("Silakan pilih atau buat perusahaan terlebih dahulu.")

# Main content area
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Dashboard", 
    "Laporan Laba Rugi & Neraca", 
    "Arus Kas & Proyeksi", 
    "KPI & Rasio Keuangan", 
    "Catatan Keuangan"
])

with tab1:
    st.header(f"{report_title}")
    
    # Financial Summary Section
    st.subheader("Ringkasan Keuangan")
    
    # Create columns for summary data
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Calculate total revenue for selected year
        total_revenue = sum(st.session_state.revenue[selected_year].values())
        st.metric("Pendapatan Tahunan", format_currency(total_revenue))
        
        # Calculate total expenses for selected year
        total_cogs = sum(st.session_state.cogs[selected_year].values())
        total_op_expenses = sum(st.session_state.op_expenses[selected_year].values())
        total_other_expenses = sum(st.session_state.other_expenses[selected_year].values())
        
        # Calculate net profit
        net_profit = total_revenue - total_cogs - total_op_expenses - total_other_expenses
        st.metric("Laba Bersih", format_currency(net_profit))
        
        # Calculate net profit margin
        net_profit_margin = calculate_net_profit_margin(net_profit, total_revenue)
        st.metric("Margin Laba Bersih", format_percentage(net_profit_margin))
    
    with col2:
        # Calculate beginning and ending balance
        op_cash_flow = sum(st.session_state.op_cash_flow[selected_year].values())
        inv_cash_flow = sum(st.session_state.inv_cash_flow[selected_year].values())
        fin_cash_flow = sum(st.session_state.fin_cash_flow[selected_year].values())
        
        net_cash_flow = op_cash_flow + inv_cash_flow + fin_cash_flow
        st.metric("Net Cash Flow", format_currency(net_cash_flow))
        
        # YoY Growth if we have previous year data
        if current_year_index < len(st.session_state.years) - 1:
            prev_year = st.session_state.years[current_year_index + 1]
            prev_revenue = sum(st.session_state.revenue[prev_year].values())
            if prev_revenue > 0:
                yoy_growth = (total_revenue - prev_revenue) / prev_revenue
                st.metric("YoY Growth", format_percentage(yoy_growth))
            else:
                st.metric("YoY Growth", "N/A")
        else:
            st.metric("YoY Growth", "N/A")
        
        st.metric("Funding Requirements", format_currency(st.session_state.funding_requirements))
    
    with col3:
        # Saldo Awal - Saldo Akhir (Beginning - Ending Balance)
        if st.session_state.current_assets.get(selected_year):
            beginning_balance = st.session_state.current_assets.get(selected_year, 0)
            ending_balance = beginning_balance + net_cash_flow
            st.metric("Beginning Balance", format_currency(beginning_balance))
            st.metric("Ending Balance", format_currency(ending_balance))
    
    # Revenue Chart
    st.subheader("Revenue Trend")
    
    if period_type == "Monthly":
        revenue_data = pd.DataFrame({
            'Period': st.session_state.periods,
            'Revenue': [st.session_state.revenue[selected_year][month] for month in st.session_state.periods]
        })
    elif period_type == "Quarterly":
        # Aggregate monthly data into quarters
        q1_revenue = sum([st.session_state.revenue[selected_year][month] for month in st.session_state.periods[:3]])
        q2_revenue = sum([st.session_state.revenue[selected_year][month] for month in st.session_state.periods[3:6]])
        q3_revenue = sum([st.session_state.revenue[selected_year][month] for month in st.session_state.periods[6:9]])
        q4_revenue = sum([st.session_state.revenue[selected_year][month] for month in st.session_state.periods[9:]])
        
        revenue_data = pd.DataFrame({
            'Period': ["Q1", "Q2", "Q3", "Q4"],
            'Revenue': [q1_revenue, q2_revenue, q3_revenue, q4_revenue]
        })
    else:  # Yearly
        revenue_data = pd.DataFrame({
            'Period': [str(year) for year in st.session_state.years],
            'Revenue': [sum(st.session_state.revenue[year].values()) for year in st.session_state.years]
        })
    
    fig = px.bar(revenue_data, x='Period', y='Revenue', title='Revenue by Period')
    st.plotly_chart(fig, use_container_width=True)
    
    # Profit & Loss Summary Chart
    st.subheader("Profit & Loss Summary")
    
    if period_type == "Yearly":
        years = st.session_state.years
        revenue = [sum(st.session_state.revenue[year].values()) for year in years]
        cogs = [sum(st.session_state.cogs[year].values()) for year in years]
        gross_profit = [r - c for r, c in zip(revenue, cogs)]
        op_expenses = [sum(st.session_state.op_expenses[year].values()) for year in years]
        other_expenses = [sum(st.session_state.other_expenses[year].values()) for year in years]
        net_profit = [g - o - oe for g, o, oe in zip(gross_profit, op_expenses, other_expenses)]
        
        fig = go.Figure()
        fig.add_trace(go.Bar(x=[str(y) for y in years], y=revenue, name='Revenue'))
        fig.add_trace(go.Bar(x=[str(y) for y in years], y=cogs, name='COGS'))
        fig.add_trace(go.Bar(x=[str(y) for y in years], y=op_expenses, name='Op. Expenses'))
        fig.add_trace(go.Bar(x=[str(y) for y in years], y=other_expenses, name='Other Expenses'))
        fig.add_trace(go.Scatter(x=[str(y) for y in years], y=net_profit, name='Net Profit', line=dict(color='green', width=3)))
        
        fig.update_layout(barmode='group', title='Yearly Profit & Loss Summary')
        st.plotly_chart(fig, use_container_width=True)
    else:
        # Similar logic for monthly or quarterly with appropriate period selection
        if period_type == "Monthly":
            periods = st.session_state.periods
        else:  # Quarterly
            periods = ["Q1", "Q2", "Q3", "Q4"]
            
        # For simplicity, let's display the current year's data
        selected_periods = periods
        
        if period_type == "Monthly":
            revenue = [st.session_state.revenue[selected_year][month] for month in selected_periods]
            cogs = [st.session_state.cogs[selected_year][month] for month in selected_periods]
            op_expenses = [st.session_state.op_expenses[selected_year][month] for month in selected_periods]
            other_expenses = [st.session_state.other_expenses[selected_year][month] for month in selected_periods]
        else:  # Quarterly
            # Aggregate monthly data into quarters for the selected year
            q1_revenue = sum([st.session_state.revenue[selected_year][month] for month in st.session_state.periods[:3]])
            q2_revenue = sum([st.session_state.revenue[selected_year][month] for month in st.session_state.periods[3:6]])
            q3_revenue = sum([st.session_state.revenue[selected_year][month] for month in st.session_state.periods[6:9]])
            q4_revenue = sum([st.session_state.revenue[selected_year][month] for month in st.session_state.periods[9:]])
            revenue = [q1_revenue, q2_revenue, q3_revenue, q4_revenue]
            
            q1_cogs = sum([st.session_state.cogs[selected_year][month] for month in st.session_state.periods[:3]])
            q2_cogs = sum([st.session_state.cogs[selected_year][month] for month in st.session_state.periods[3:6]])
            q3_cogs = sum([st.session_state.cogs[selected_year][month] for month in st.session_state.periods[6:9]])
            q4_cogs = sum([st.session_state.cogs[selected_year][month] for month in st.session_state.periods[9:]])
            cogs = [q1_cogs, q2_cogs, q3_cogs, q4_cogs]
            
            q1_op_expenses = sum([st.session_state.op_expenses[selected_year][month] for month in st.session_state.periods[:3]])
            q2_op_expenses = sum([st.session_state.op_expenses[selected_year][month] for month in st.session_state.periods[3:6]])
            q3_op_expenses = sum([st.session_state.op_expenses[selected_year][month] for month in st.session_state.periods[6:9]])
            q4_op_expenses = sum([st.session_state.op_expenses[selected_year][month] for month in st.session_state.periods[9:]])
            op_expenses = [q1_op_expenses, q2_op_expenses, q3_op_expenses, q4_op_expenses]
            
            q1_other_expenses = sum([st.session_state.other_expenses[selected_year][month] for month in st.session_state.periods[:3]])
            q2_other_expenses = sum([st.session_state.other_expenses[selected_year][month] for month in st.session_state.periods[3:6]])
            q3_other_expenses = sum([st.session_state.other_expenses[selected_year][month] for month in st.session_state.periods[6:9]])
            q4_other_expenses = sum([st.session_state.other_expenses[selected_year][month] for month in st.session_state.periods[9:]])
            other_expenses = [q1_other_expenses, q2_other_expenses, q3_other_expenses, q4_other_expenses]
            
        gross_profit = [r - c for r, c in zip(revenue, cogs)]
        net_profit = [g - o - oe for g, o, oe in zip(gross_profit, op_expenses, other_expenses)]
        
        fig = go.Figure()
        fig.add_trace(go.Bar(x=selected_periods, y=revenue, name='Revenue'))
        fig.add_trace(go.Bar(x=selected_periods, y=cogs, name='COGS'))
        fig.add_trace(go.Bar(x=selected_periods, y=op_expenses, name='Op. Expenses'))
        fig.add_trace(go.Bar(x=selected_periods, y=other_expenses, name='Other Expenses'))
        fig.add_trace(go.Scatter(x=selected_periods, y=net_profit, name='Net Profit', line=dict(color='green', width=3)))
        
        title_period = "Monthly" if period_type == "Monthly" else "Quarterly"
        fig.update_layout(barmode='group', title=f'{title_period} Profit & Loss Summary ({selected_year})')
        st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.header("Income Statement & Balance Sheet")
    
    # Income Statement Input Section
    with st.expander("Income Statement Data Input"):
        st.subheader("Income Statement Data")
        
        # Year Selection for data input
        input_year = st.selectbox("Select Year for Data Input", st.session_state.years, key="income_year")
        
        # Create columns for input
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Revenue & COGS")
            for month in st.session_state.periods:
                col_a, col_b = st.columns(2)
                with col_a:
                    st.session_state.revenue[input_year][month] = st.number_input(
                        f"Revenue - {month} {input_year}", 
                        value=st.session_state.revenue[input_year][month],
                        key=f"revenue_{input_year}_{month}"
                    )
                with col_b:
                    st.session_state.cogs[input_year][month] = st.number_input(
                        f"COGS - {month} {input_year}", 
                        value=st.session_state.cogs[input_year][month],
                        key=f"cogs_{input_year}_{month}"
                    )
        
        with col2:
            st.subheader("Expenses")
            for month in st.session_state.periods:
                col_a, col_b = st.columns(2)
                with col_a:
                    st.session_state.op_expenses[input_year][month] = st.number_input(
                        f"Op. Expenses - {month} {input_year}", 
                        value=st.session_state.op_expenses[input_year][month],
                        key=f"op_expenses_{input_year}_{month}"
                    )
                with col_b:
                    st.session_state.other_expenses[input_year][month] = st.number_input(
                        f"Other Expenses - {month} {input_year}", 
                        value=st.session_state.other_expenses[input_year][month],
                        key=f"other_expenses_{input_year}_{month}"
                    )
        
        # Tax Rate Input
        st.session_state.tax_rate = st.slider("Tax Rate (%)", 0.0, 100.0, float(st.session_state.tax_rate * 100)) / 100

    # Balance Sheet Input Section
    with st.expander("Balance Sheet Data Input"):
        st.subheader("Balance Sheet Data")
        
        # Year Selection for balance sheet data input
        bs_input_year = st.selectbox("Select Year for Balance Sheet Data", st.session_state.years, key="bs_year")
        
        # Create columns for input
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Assets")
            st.session_state.current_assets[bs_input_year] = st.number_input(
                f"Current Assets {bs_input_year}", 
                value=st.session_state.current_assets[bs_input_year],
                key=f"current_assets_{bs_input_year}"
            )
            st.session_state.fixed_assets[bs_input_year] = st.number_input(
                f"Fixed Assets {bs_input_year}", 
                value=st.session_state.fixed_assets[bs_input_year],
                key=f"fixed_assets_{bs_input_year}"
            )
        
        with col2:
            st.subheader("Liabilities & Equity")
            st.session_state.short_term_liabilities[bs_input_year] = st.number_input(
                f"Short-term Liabilities {bs_input_year}", 
                value=st.session_state.short_term_liabilities[bs_input_year],
                key=f"short_term_liabilities_{bs_input_year}"
            )
            st.session_state.long_term_liabilities[bs_input_year] = st.number_input(
                f"Long-term Liabilities {bs_input_year}", 
                value=st.session_state.long_term_liabilities[bs_input_year],
                key=f"long_term_liabilities_{bs_input_year}"
            )
            st.session_state.owner_equity[bs_input_year] = st.number_input(
                f"Owner's Equity {bs_input_year}", 
                value=st.session_state.owner_equity[bs_input_year],
                key=f"owner_equity_{bs_input_year}"
            )
            st.session_state.retained_earnings[bs_input_year] = st.number_input(
                f"Retained Earnings {bs_input_year}", 
                value=st.session_state.retained_earnings[bs_input_year],
                key=f"retained_earnings_{bs_input_year}"
            )
    
    # Display Income Statement
    st.subheader(f"Income Statement ({period_type} - {selected_year})")
    
    # Create income statement dataframe based on period type
    if period_type == "Monthly":
        periods = st.session_state.periods
        revenue = [st.session_state.revenue[selected_year][month] for month in periods]
        cogs = [st.session_state.cogs[selected_year][month] for month in periods]
        gross_profit = [r - c for r, c in zip(revenue, cogs)]
        op_expenses = [st.session_state.op_expenses[selected_year][month] for month in periods]
        operating_profit = [g - o for g, o in zip(gross_profit, op_expenses)]
        other_expenses = [st.session_state.other_expenses[selected_year][month] for month in periods]
        profit_before_tax = [op - oe for op, oe in zip(operating_profit, other_expenses)]
        tax = [p * st.session_state.tax_rate for p in profit_before_tax]
        net_profit = [p - t for p, t in zip(profit_before_tax, tax)]
        
        income_data = pd.DataFrame({
            'Period': periods,
            'Revenue': revenue,
            'COGS': cogs,
            'Gross Profit': gross_profit,
            'Operational Expenses': op_expenses,
            'Operating Profit': operating_profit,
            'Other Expenses': other_expenses,
            'Profit Before Tax': profit_before_tax,
            'Tax': tax,
            'Net Profit': net_profit
        })
    elif period_type == "Quarterly":
        # Aggregate monthly data into quarters
        quarters = ["Q1", "Q2", "Q3", "Q4"]
        quarter_months = [st.session_state.periods[:3], st.session_state.periods[3:6], 
                         st.session_state.periods[6:9], st.session_state.periods[9:]]
        
        revenue = []
        cogs = []
        op_expenses = []
        other_expenses = []
        
        for q_months in quarter_months:
            q_revenue = sum([st.session_state.revenue[selected_year][month] for month in q_months])
            revenue.append(q_revenue)
            
            q_cogs = sum([st.session_state.cogs[selected_year][month] for month in q_months])
            cogs.append(q_cogs)
            
            q_op_expenses = sum([st.session_state.op_expenses[selected_year][month] for month in q_months])
            op_expenses.append(q_op_expenses)
            
            q_other_expenses = sum([st.session_state.other_expenses[selected_year][month] for month in q_months])
            other_expenses.append(q_other_expenses)
        
        gross_profit = [r - c for r, c in zip(revenue, cogs)]
        operating_profit = [g - o for g, o in zip(gross_profit, op_expenses)]
        profit_before_tax = [op - oe for op, oe in zip(operating_profit, other_expenses)]
        tax = [p * st.session_state.tax_rate for p in profit_before_tax]
        net_profit = [p - t for p, t in zip(profit_before_tax, tax)]
        
        income_data = pd.DataFrame({
            'Period': quarters,
            'Revenue': revenue,
            'COGS': cogs,
            'Gross Profit': gross_profit,
            'Operational Expenses': op_expenses,
            'Operating Profit': operating_profit,
            'Other Expenses': other_expenses,
            'Profit Before Tax': profit_before_tax,
            'Tax': tax,
            'Net Profit': net_profit
        })
    else:  # Yearly
        years = st.session_state.years
        revenue = [sum(st.session_state.revenue[year].values()) for year in years]
        cogs = [sum(st.session_state.cogs[year].values()) for year in years]
        gross_profit = [r - c for r, c in zip(revenue, cogs)]
        op_expenses = [sum(st.session_state.op_expenses[year].values()) for year in years]
        operating_profit = [g - o for g, o in zip(gross_profit, op_expenses)]
        other_expenses = [sum(st.session_state.other_expenses[year].values()) for year in years]
        profit_before_tax = [op - oe for op, oe in zip(operating_profit, other_expenses)]
        tax = [p * st.session_state.tax_rate for p in profit_before_tax]
        net_profit = [p - t for p, t in zip(profit_before_tax, tax)]
        
        income_data = pd.DataFrame({
            'Period': [str(year) for year in years],
            'Revenue': revenue,
            'COGS': cogs,
            'Gross Profit': gross_profit,
            'Operational Expenses': op_expenses,
            'Operating Profit': operating_profit,
            'Other Expenses': other_expenses,
            'Profit Before Tax': profit_before_tax,
            'Tax': tax,
            'Net Profit': net_profit
        })
    
    # Format currency columns
    for col in income_data.columns:
        if col != 'Period':
            income_data[col] = income_data[col].apply(lambda x: format_currency(x))
    
    st.table(income_data)
    
    # Display visualizations for income statement
    col1, col2 = st.columns(2)
    
    with col1:
        # Convert formatted currency back to numeric for charts
        numeric_data = income_data.copy()
        for col in numeric_data.columns:
            if col != 'Period':
                numeric_data[col] = numeric_data[col].str.replace('Rp', '').str.replace(',', '').astype(float)
        
        fig = px.bar(numeric_data, x='Period', y=['Revenue', 'COGS', 'Operational Expenses', 'Other Expenses'], 
                    title='Revenue vs. Expenses')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig = px.line(numeric_data, x='Period', y=['Gross Profit', 'Operating Profit', 'Net Profit'], 
                     title='Profit Trends')
        st.plotly_chart(fig, use_container_width=True)
    
    # Display Balance Sheet
    st.subheader(f"Balance Sheet (as of {selected_year})")
    
    # Calculate total assets, liabilities, and equity
    total_assets = st.session_state.current_assets[selected_year] + st.session_state.fixed_assets[selected_year]
    total_liabilities = st.session_state.short_term_liabilities[selected_year] + st.session_state.long_term_liabilities[selected_year]
    total_equity = st.session_state.owner_equity[selected_year] + st.session_state.retained_earnings[selected_year]
    
    # Create balance sheet dataframe
    balance_sheet_data = pd.DataFrame({
        'Category': ['Assets', 'Current Assets', 'Fixed Assets', 'Total Assets', 
                    'Liabilities', 'Short-term Liabilities', 'Long-term Liabilities', 'Total Liabilities',
                    'Equity', "Owner's Equity", 'Retained Earnings', 'Total Equity',
                    'Total Liabilities & Equity'],
        'Amount': ['', format_currency(st.session_state.current_assets[selected_year]), 
                  format_currency(st.session_state.fixed_assets[selected_year]), format_currency(total_assets),
                  '', format_currency(st.session_state.short_term_liabilities[selected_year]), 
                  format_currency(st.session_state.long_term_liabilities[selected_year]), format_currency(total_liabilities),
                  '', format_currency(st.session_state.owner_equity[selected_year]), 
                  format_currency(st.session_state.retained_earnings[selected_year]), format_currency(total_equity),
                  format_currency(total_liabilities + total_equity)]
    })
    
    # Display balance sheet
    st.table(balance_sheet_data)
    
    # Visualize balance sheet
    col1, col2 = st.columns(2)
    
    with col1:
        # Create pie chart for assets
        assets_labels = ['Current Assets', 'Fixed Assets']
        assets_values = [st.session_state.current_assets[selected_year], st.session_state.fixed_assets[selected_year]]
        
        fig = px.pie(values=assets_values, names=assets_labels, title='Assets Breakdown')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Create pie chart for liabilities and equity
        liab_equity_labels = ['Short-term Liabilities', 'Long-term Liabilities', "Owner's Equity", 'Retained Earnings']
        liab_equity_values = [st.session_state.short_term_liabilities[selected_year], 
                            st.session_state.long_term_liabilities[selected_year],
                            st.session_state.owner_equity[selected_year], 
                            st.session_state.retained_earnings[selected_year]]
        
        fig = px.pie(values=liab_equity_values, names=liab_equity_labels, title='Liabilities & Equity Breakdown')
        st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.header("Cash Flow & Projections")
    
    # Cash Flow Input Section
    with st.expander("Cash Flow Data Input"):
        st.subheader("Cash Flow Data")
        
        # Year Selection for cash flow data input
        cf_input_year = st.selectbox("Select Year for Cash Flow Data", st.session_state.years, key="cf_year")
        
        # Create columns for input
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.subheader("Operational Cash Flow")
            for month in st.session_state.periods:
                st.session_state.op_cash_flow[cf_input_year][month] = st.number_input(
                    f"Op. Cash Flow - {month} {cf_input_year}", 
                    value=st.session_state.op_cash_flow[cf_input_year][month],
                    key=f"op_cash_flow_{cf_input_year}_{month}"
                )
        
        with col2:
            st.subheader("Investment Cash Flow")
            for month in st.session_state.periods:
                st.session_state.inv_cash_flow[cf_input_year][month] = st.number_input(
                    f"Inv. Cash Flow - {month} {cf_input_year}", 
                    value=st.session_state.inv_cash_flow[cf_input_year][month],
                    key=f"inv_cash_flow_{cf_input_year}_{month}"
                )
        
        with col3:
            st.subheader("Financing Cash Flow")
            for month in st.session_state.periods:
                st.session_state.fin_cash_flow[cf_input_year][month] = st.number_input(
                    f"Fin. Cash Flow - {month} {cf_input_year}", 
                    value=st.session_state.fin_cash_flow[cf_input_year][month],
                    key=f"fin_cash_flow_{cf_input_year}_{month}"
                )
    
    # Financial Projections Input
    with st.expander("Financial Projections Input"):
        st.subheader("Projection Parameters")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.session_state.revenue_growth = st.slider(
                "Revenue Growth Rate (%)", 
                -20.0, 100.0, 
                float(st.session_state.revenue_growth * 100)
            ) / 100
        
        with col2:
            st.session_state.expense_growth = st.slider(
                "Expense Growth Rate (%)", 
                -20.0, 100.0, 
                float(st.session_state.expense_growth * 100)
            ) / 100
        
        with col3:
            st.session_state.projection_years = st.number_input(
                "Projection Years", 
                min_value=1, max_value=5, 
                value=st.session_state.projection_years
            )
    
    # Display Cash Flow Statement
    st.subheader(f"Cash Flow Statement ({period_type} - {selected_year})")
    
    # Create cash flow dataframe based on period type
    if period_type == "Monthly":
        periods = st.session_state.periods
        op_cash = [st.session_state.op_cash_flow[selected_year][month] for month in periods]
        inv_cash = [st.session_state.inv_cash_flow[selected_year][month] for month in periods]
        fin_cash = [st.session_state.fin_cash_flow[selected_year][month] for month in periods]
        net_cash = [o + i + f for o, i, f in zip(op_cash, inv_cash, fin_cash)]
        
        cash_flow_data = pd.DataFrame({
            'Period': periods,
            'Operational Cash Flow': op_cash,
            'Investment Cash Flow': inv_cash,
            'Financing Cash Flow': fin_cash,
            'Net Cash Flow': net_cash
        })
    elif period_type == "Quarterly":
        # Aggregate monthly data into quarters
        quarters = ["Q1", "Q2", "Q3", "Q4"]
        quarter_months = [st.session_state.periods[:3], st.session_state.periods[3:6], 
                         st.session_state.periods[6:9], st.session_state.periods[9:]]
        
        op_cash = []
        inv_cash = []
        fin_cash = []
        
        for q_months in quarter_months:
            q_op_cash = sum([st.session_state.op_cash_flow[selected_year][month] for month in q_months])
            op_cash.append(q_op_cash)
            
            q_inv_cash = sum([st.session_state.inv_cash_flow[selected_year][month] for month in q_months])
            inv_cash.append(q_inv_cash)
            
            q_fin_cash = sum([st.session_state.fin_cash_flow[selected_year][month] for month in q_months])
            fin_cash.append(q_fin_cash)
        
        net_cash = [o + i + f for o, i, f in zip(op_cash, inv_cash, fin_cash)]
        
        cash_flow_data = pd.DataFrame({
            'Period': quarters,
            'Operational Cash Flow': op_cash,
            'Investment Cash Flow': inv_cash,
            'Financing Cash Flow': fin_cash,
            'Net Cash Flow': net_cash
        })
    else:  # Yearly
        years = st.session_state.years
        op_cash = [sum(st.session_state.op_cash_flow[year].values()) for year in years]
        inv_cash = [sum(st.session_state.inv_cash_flow[year].values()) for year in years]
        fin_cash = [sum(st.session_state.fin_cash_flow[year].values()) for year in years]
        net_cash = [o + i + f for o, i, f in zip(op_cash, inv_cash, fin_cash)]
        
        cash_flow_data = pd.DataFrame({
            'Period': [str(year) for year in years],
            'Operational Cash Flow': op_cash,
            'Investment Cash Flow': inv_cash,
            'Financing Cash Flow': fin_cash,
            'Net Cash Flow': net_cash
        })
    
    # Format currency columns
    for col in cash_flow_data.columns:
        if col != 'Period':
            cash_flow_data[col] = cash_flow_data[col].apply(lambda x: format_currency(x))
    
    st.table(cash_flow_data)
    
    # Visualize cash flow
    # Convert formatted currency back to numeric for charts
    numeric_data = cash_flow_data.copy()
    for col in numeric_data.columns:
        if col != 'Period':
            numeric_data[col] = numeric_data[col].str.replace('Rp', '').str.replace(',', '').astype(float)
    
    fig = px.bar(numeric_data, x='Period', y=['Operational Cash Flow', 'Investment Cash Flow', 'Financing Cash Flow'], 
                title='Cash Flow Components')
    fig.add_trace(go.Scatter(x=numeric_data['Period'], y=numeric_data['Net Cash Flow'], 
                            mode='lines+markers', name='Net Cash Flow', line=dict(color='green', width=3)))
    st.plotly_chart(fig, use_container_width=True)
    
    # Display Financial Projections
    st.subheader("Financial Projections")
    
    # Calculate projections based on the latest year data
    current_year = selected_year
    current_year_revenue = sum(st.session_state.revenue[current_year].values())
    current_year_expenses = (sum(st.session_state.cogs[current_year].values()) + 
                           sum(st.session_state.op_expenses[current_year].values()) + 
                           sum(st.session_state.other_expenses[current_year].values()))
    
    projection_years = [current_year + i for i in range(1, st.session_state.projection_years + 1)]
    projected_revenue = [current_year_revenue * (1 + st.session_state.revenue_growth) ** i for i in range(1, st.session_state.projection_years + 1)]
    projected_expenses = [current_year_expenses * (1 + st.session_state.expense_growth) ** i for i in range(1, st.session_state.projection_years + 1)]
    projected_profit = [r - e for r, e in zip(projected_revenue, projected_expenses)]
    
    projection_data = pd.DataFrame({
        'Year': projection_years,
        'Projected Revenue': [format_currency(r) for r in projected_revenue],
        'Projected Expenses': [format_currency(e) for e in projected_expenses],
        'Projected Net Profit': [format_currency(p) for p in projected_profit]
    })
    
    st.table(projection_data)
    
    # Visualize projections
    # Add current year data for context
    all_years = [current_year] + projection_years
    all_revenue = [current_year_revenue] + projected_revenue
    all_expenses = [current_year_expenses] + projected_expenses
    all_profit = [current_year_revenue - current_year_expenses] + projected_profit
    
    fig = go.Figure()
    fig.add_trace(go.Bar(x=[str(y) for y in all_years], y=all_revenue, name='Revenue'))
    fig.add_trace(go.Bar(x=[str(y) for y in all_years], y=all_expenses, name='Expenses'))
    fig.add_trace(go.Scatter(x=[str(y) for y in all_years], y=all_profit, name='Net Profit', 
                          line=dict(color='green', width=3)))
    
    fig.update_layout(title='Financial Projections', barmode='group')
    st.plotly_chart(fig, use_container_width=True)
    
    # Break-even Analysis
    st.subheader("Break-even Analysis")
    
    # Simple break-even analysis based on current year data
    fixed_costs = sum(st.session_state.op_expenses[current_year].values())
    total_revenue = sum(st.session_state.revenue[current_year].values())
    total_variable_costs = sum(st.session_state.cogs[current_year].values())
    
    # Avoid division by zero
    if total_revenue > 0:
        contribution_margin_ratio = (total_revenue - total_variable_costs) / total_revenue
        if contribution_margin_ratio > 0:
            break_even_revenue = fixed_costs / contribution_margin_ratio
            
            st.write(f"Based on current year data:")
            st.write(f"Fixed Costs: {format_currency(fixed_costs)}")
            st.write(f"Contribution Margin Ratio: {format_percentage(contribution_margin_ratio)}")
            st.write(f"Break-even Revenue: {format_currency(break_even_revenue)}")
            
            # Create a break-even chart
            revenue_range = np.linspace(0, total_revenue * 2, 100)
            total_costs = fixed_costs + (1 - contribution_margin_ratio) * revenue_range
            profit = revenue_range - total_costs
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=revenue_range, y=revenue_range, name='Revenue', line=dict(color='blue')))
            fig.add_trace(go.Scatter(x=revenue_range, y=total_costs, name='Total Costs', line=dict(color='red')))
            fig.add_trace(go.Scatter(x=revenue_range, y=np.repeat(fixed_costs, len(revenue_range)), 
                                    name='Fixed Costs', line=dict(color='green', dash='dash')))
            
            # Mark the break-even point
            fig.add_trace(go.Scatter(x=[break_even_revenue], y=[break_even_revenue], 
                                    mode='markers', name='Break-even Point', 
                                    marker=dict(color='purple', size=12)))
            
            fig.update_layout(title='Break-even Analysis', xaxis_title='Revenue', yaxis_title='Costs/Revenue')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Cannot calculate break-even point because the contribution margin is negative or zero.")
    else:
        st.warning("Cannot calculate break-even point because revenue is zero.")
    
    # Sensitivity Analysis
    st.subheader("Sensitivity Analysis")
    
    # Create a sensitivity analysis for revenue growth vs expense growth impact on profit
    growth_scenarios = [-0.1, -0.05, 0, 0.05, 0.1, 0.15, 0.2]
    
    # Calculate profit for different combinations of revenue and expense growth
    sensitivity_results = []
    
    for rev_g in growth_scenarios:
        row = []
        for exp_g in growth_scenarios:
            # Project one year ahead with these growth rates
            proj_revenue = current_year_revenue * (1 + rev_g)
            proj_expenses = current_year_expenses * (1 + exp_g)
            proj_profit = proj_revenue - proj_expenses
            row.append(proj_profit)
        sensitivity_results.append(row)
    
    # Create a dataframe for the sensitivity analysis
    sensitivity_df = pd.DataFrame(sensitivity_results, 
                                 index=[f"Rev {format_percentage(g)}" for g in growth_scenarios],
                                 columns=[f"Exp {format_percentage(g)}" for g in growth_scenarios])
    
    # Format as currency
    for col in sensitivity_df.columns:
        sensitivity_df[col] = sensitivity_df[col].apply(lambda x: format_currency(x))
    
    st.write("Impact of Different Growth Scenarios on Projected Profit:")
    st.table(sensitivity_df)

with tab4:
    st.header("KPIs & Financial Ratios")
    
    # KPI Input Section
    with st.expander("KPI Data Input"):
        st.subheader("Key Performance Indicators")
        
        # Year Selection for KPI data input
        kpi_input_year = st.selectbox("Select Year for KPI Data", st.session_state.years, key="kpi_year")
        
        # Create columns for input
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.session_state.cac[kpi_input_year] = st.number_input(
                f"Customer Acquisition Cost (CAC) {kpi_input_year}", 
                value=st.session_state.cac[kpi_input_year],
                key=f"cac_{kpi_input_year}"
            )
        
        with col2:
            st.session_state.ltv[kpi_input_year] = st.number_input(
                f"Lifetime Value (LTV) {kpi_input_year}", 
                value=st.session_state.ltv[kpi_input_year],
                key=f"ltv_{kpi_input_year}"
            )
        
        with col3:
            st.session_state.burn_rate[kpi_input_year] = st.number_input(
                f"Burn Rate {kpi_input_year}", 
                value=st.session_state.burn_rate[kpi_input_year],
                key=f"burn_rate_{kpi_input_year}"
            )
    
    # Display KPIs
    st.subheader(f"Key Performance Indicators ({selected_year})")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Gross Margin
        total_revenue = sum(st.session_state.revenue[selected_year].values())
        total_cogs = sum(st.session_state.cogs[selected_year].values())
        gross_margin = calculate_gross_margin(total_revenue, total_cogs)
        
        st.metric("Gross Margin", format_percentage(gross_margin))
        
        # CAC
        st.metric("Customer Acquisition Cost", format_currency(st.session_state.cac[selected_year]))
    
    with col2:
        # Net Profit Margin
        total_expenses = (total_cogs + 
                        sum(st.session_state.op_expenses[selected_year].values()) + 
                        sum(st.session_state.other_expenses[selected_year].values()))
        net_profit = total_revenue - total_expenses
        net_profit_margin = calculate_net_profit_margin(net_profit, total_revenue)
        
        st.metric("Net Profit Margin", format_percentage(net_profit_margin))
        
        # LTV
        st.metric("Lifetime Value", format_currency(st.session_state.ltv[selected_year]))
    
    with col3:
        # Burn Rate
        st.metric("Burn Rate", format_currency(st.session_state.burn_rate[selected_year]))
        
        # LTV:CAC Ratio
        if st.session_state.cac[selected_year] > 0:
            ltv_cac_ratio = st.session_state.ltv[selected_year] / st.session_state.cac[selected_year]
            st.metric("LTV:CAC Ratio", f"{ltv_cac_ratio:.2f}")
        else:
            st.metric("LTV:CAC Ratio", "N/A")
    
    # Display Financial Ratios
    st.subheader(f"Financial Ratios ({selected_year})")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Current Ratio
        current_assets = st.session_state.current_assets[selected_year]
        short_term_liabilities = st.session_state.short_term_liabilities[selected_year]
        current_ratio = calculate_current_ratio(current_assets, short_term_liabilities)
        
        st.metric("Current Ratio", f"{current_ratio:.2f}")
    
    with col2:
        # Debt-to-Equity Ratio
        total_liabilities = st.session_state.short_term_liabilities[selected_year] + st.session_state.long_term_liabilities[selected_year]
        total_equity = st.session_state.owner_equity[selected_year] + st.session_state.retained_earnings[selected_year]
        debt_to_equity = calculate_debt_to_equity(total_liabilities, total_equity)
        
        st.metric("Debt-to-Equity Ratio", f"{debt_to_equity:.2f}")
    
    # KPI Trends
    st.subheader("KPI Trends")
    
    # Create dataframes for KPI trends
    years = st.session_state.years
    
    # Calculate KPIs for all years
    gross_margins = []
    net_profit_margins = []
    current_ratios = []
    debt_to_equity_ratios = []
    
    for year in years:
        # Gross Margin
        revenue = sum(st.session_state.revenue[year].values())
        cogs = sum(st.session_state.cogs[year].values())
        gross_margins.append(calculate_gross_margin(revenue, cogs))
        
        # Net Profit Margin
        op_expenses = sum(st.session_state.op_expenses[year].values())
        other_expenses = sum(st.session_state.other_expenses[year].values())
        net_profit = revenue - cogs - op_expenses - other_expenses
        net_profit_margins.append(calculate_net_profit_margin(net_profit, revenue))
        
        # Current Ratio
        current_assets = st.session_state.current_assets[year]
        short_term_liabilities = st.session_state.short_term_liabilities[year]
        current_ratios.append(calculate_current_ratio(current_assets, short_term_liabilities))
        
        # Debt-to-Equity Ratio
        total_liabilities = st.session_state.short_term_liabilities[year] + st.session_state.long_term_liabilities[year]
        total_equity = st.session_state.owner_equity[year] + st.session_state.retained_earnings[year]
        debt_to_equity_ratios.append(calculate_debt_to_equity(total_liabilities, total_equity))
    
    # Create chart for margin trends
    col1, col2 = st.columns(2)
    
    with col1:
        margin_data = pd.DataFrame({
            'Year': [str(year) for year in years],
            'Gross Margin': [m * 100 for m in gross_margins],
            'Net Profit Margin': [m * 100 for m in net_profit_margins]
        })
        
        fig = px.line(margin_data, x='Year', y=['Gross Margin', 'Net Profit Margin'], 
                     title='Margin Trends (%)')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        ratio_data = pd.DataFrame({
            'Year': [str(year) for year in years],
            'Current Ratio': current_ratios,
            'Debt-to-Equity Ratio': debt_to_equity_ratios
        })
        
        fig = px.line(ratio_data, x='Year', y=['Current Ratio', 'Debt-to-Equity Ratio'], 
                     title='Financial Ratio Trends')
        st.plotly_chart(fig, use_container_width=True)
    
    # CAC and LTV trends
    cac_data = [st.session_state.cac[year] for year in years]
    ltv_data = [st.session_state.ltv[year] for year in years]
    burn_rate_data = [st.session_state.burn_rate[year] for year in years]
    
    col1, col2 = st.columns(2)
    
    with col1:
        cac_ltv_data = pd.DataFrame({
            'Year': [str(year) for year in years],
            'CAC': cac_data,
            'LTV': ltv_data
        })
        
        fig = px.bar(cac_ltv_data, x='Year', y=['CAC', 'LTV'], title='CAC vs LTV Trend', barmode='group')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Calculate LTV:CAC ratio
        ltv_cac_ratio = []
        for cac, ltv in zip(cac_data, ltv_data):
            if cac > 0:
                ltv_cac_ratio.append(ltv / cac)
            else:
                ltv_cac_ratio.append(0)
        
        ratio_data = pd.DataFrame({
            'Year': [str(year) for year in years],
            'LTV:CAC Ratio': ltv_cac_ratio,
            'Burn Rate': burn_rate_data
        })
        
        fig = go.Figure()
        fig.add_trace(go.Bar(x=ratio_data['Year'], y=ratio_data['Burn Rate'], name='Burn Rate'))
        fig.add_trace(go.Scatter(x=ratio_data['Year'], y=ratio_data['LTV:CAC Ratio'], 
                              mode='lines+markers', name='LTV:CAC Ratio', yaxis='y2'))
        
        fig.update_layout(
            title='Burn Rate and LTV:CAC Ratio',
            yaxis=dict(title='Burn Rate ($)'),
            yaxis2=dict(title='LTV:CAC Ratio', overlaying='y', side='right')
        )
        
        st.plotly_chart(fig, use_container_width=True)

with tab5:
    st.header("Financial Notes & Funding Information")
    
    # Financial Notes Input
    with st.expander("Financial Notes Input"):
        st.subheader("Notes & Explanation")
        
        st.session_state.growth_strategy = st.text_area(
            "Growth Strategy", 
            value=st.session_state.growth_strategy,
            height=150
        )
        
        st.session_state.business_risks = st.text_area(
            "Business Risks & Mitigation", 
            value=st.session_state.business_risks,
            height=150
        )
        
        st.session_state.anomalies = st.text_area(
            "Explanation of Significant Variations", 
            value=st.session_state.anomalies,
            height=150
        )
    
    # Funding Requirements Input
    with st.expander("Funding Information Input"):
        st.subheader("Funding Requirements & Allocation")
        
        st.session_state.funding_requirements = st.number_input(
            "Funding Requirements ($)", 
            value=st.session_state.funding_requirements,
            key="funding_req"
        )
        
        st.session_state.funding_allocation = st.text_area(
            "Funding Allocation (Use of Funds)", 
            value=st.session_state.funding_allocation,
            height=150
        )
    
    # Display Financial Notes
    st.subheader("Financial Notes")
    
    # Growth Strategy
    st.write("##### Growth Strategy")
    if st.session_state.growth_strategy:
        st.write(st.session_state.growth_strategy)
    else:
        st.write("No growth strategy information provided.")
    
    # Business Risks
    st.write("##### Business Risks & Mitigation")
    if st.session_state.business_risks:
        st.write(st.session_state.business_risks)
    else:
        st.write("No business risk information provided.")
    
    # Explanation of Variations
    st.write("##### Explanation of Significant Variations")
    if st.session_state.anomalies:
        st.write(st.session_state.anomalies)
    else:
        st.write("No information about significant variations provided.")
    
    # Display Funding Information
    st.subheader("Funding Requirements & Allocation")
    
    # Funding Requirements
    st.write("##### Funding Requirements")
    st.write(f"Total Funding Required: {format_currency(st.session_state.funding_requirements)}")
    
    # Funding Allocation
    st.write("##### Use of Funds")
    if st.session_state.funding_allocation:
        st.write(st.session_state.funding_allocation)
    else:
        st.write("No funding allocation information provided.")
    
    # If funding allocation details are provided, we can visualize it
    # This is a placeholder for when allocation details are available in a structured format
    if st.session_state.funding_allocation:
        # For example purposes, we'll create a sample visualization
        # In a real implementation, this would parse the allocation text or use structured data
        st.write("##### Sample Funding Allocation Visualization")
        st.warning("This is a sample visualization. Update it with actual allocation data once available.")
        
        # Sample allocation data
        allocation_labels = ['R&D', 'Marketing', 'Operations', 'Working Capital', 'Other']
        allocation_values = [30, 25, 20, 15, 10]  # percentages
        
        fig = px.pie(values=allocation_values, names=allocation_labels, 
                    title='Funding Allocation (Sample)')
        st.plotly_chart(fig, use_container_width=True)

# PDF Export functionality
st.markdown("---")
st.subheader("Export Report")

if st.button("Generate PDF Report"):
    with st.spinner("Generating PDF report..."):
        try:
            # Get report data
            report_data = {
                "title": report_title,
                "selected_year": selected_year,
                "selected_period": selected_period,
                "period_type": period_type,
                "revenue": st.session_state.revenue,
                "cogs": st.session_state.cogs,
                "op_expenses": st.session_state.op_expenses,
                "other_expenses": st.session_state.other_expenses,
                "current_assets": st.session_state.current_assets,
                "fixed_assets": st.session_state.fixed_assets,
                "short_term_liabilities": st.session_state.short_term_liabilities,
                "long_term_liabilities": st.session_state.long_term_liabilities,
                "owner_equity": st.session_state.owner_equity,
                "retained_earnings": st.session_state.retained_earnings,
                "op_cash_flow": st.session_state.op_cash_flow,
                "inv_cash_flow": st.session_state.inv_cash_flow,
                "fin_cash_flow": st.session_state.fin_cash_flow,
                "cac": st.session_state.cac,
                "ltv": st.session_state.ltv,
                "burn_rate": st.session_state.burn_rate,
                "growth_strategy": st.session_state.growth_strategy,
                "business_risks": st.session_state.business_risks,
                "anomalies": st.session_state.anomalies,
                "funding_requirements": st.session_state.funding_requirements,
                "funding_allocation": st.session_state.funding_allocation,
                "tax_rate": st.session_state.tax_rate,
                "periods": st.session_state.periods,
                "years": st.session_state.years
            }
            
            # Generate PDF
            pdf_bytes = generate_pdf(report_data)
            
            # Create download button
            st.download_button(
                label="Download PDF Report",
                data=pdf_bytes,
                file_name=f"{report_title}_{selected_year}.pdf",
                mime="application/pdf"
            )
            
            st.success("PDF generated successfully!")
        except Exception as e:
            st.error(f"An error occurred while generating the PDF: {str(e)}")
