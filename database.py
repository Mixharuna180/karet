import os
import streamlit as st
from sqlalchemy import create_engine, Column, Integer, Float, String, Date, ForeignKey, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import datetime

# Dapatkan connection string database dari environment variable
DATABASE_URL = os.environ.get("DATABASE_URL")

# Buat engine untuk koneksi ke database
engine = create_engine(DATABASE_URL)

# Buat base class untuk model SQLAlchemy
Base = declarative_base()

# Definisikan model/tabel
class Company(Base):
    __tablename__ = 'companies'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    industry = Column(String)
    founded_date = Column(Date)
    
    # Relationships
    financial_data = relationship("FinancialData", back_populates="company", cascade="all, delete-orphan")
    balance_sheets = relationship("BalanceSheet", back_populates="company", cascade="all, delete-orphan")
    cash_flows = relationship("CashFlow", back_populates="company", cascade="all, delete-orphan")
    kpis = relationship("KPI", back_populates="company", cascade="all, delete-orphan")
    financial_notes = relationship("FinancialNote", back_populates="company", cascade="all, delete-orphan")

class FinancialData(Base):
    __tablename__ = 'financial_data'
    
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False)
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    revenue = Column(Float, default=0)
    cogs = Column(Float, default=0)
    operational_expenses = Column(Float, default=0)
    other_expenses = Column(Float, default=0)
    tax_rate = Column(Float, default=0.2)
    
    # Relationship
    company = relationship("Company", back_populates="financial_data")

class BalanceSheet(Base):
    __tablename__ = 'balance_sheets'
    
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False)
    year = Column(Integer, nullable=False)
    current_assets = Column(Float, default=0)
    fixed_assets = Column(Float, default=0)
    short_term_liabilities = Column(Float, default=0)
    long_term_liabilities = Column(Float, default=0)
    owner_equity = Column(Float, default=0)
    retained_earnings = Column(Float, default=0)
    
    # Relationship
    company = relationship("Company", back_populates="balance_sheets")

class CashFlow(Base):
    __tablename__ = 'cash_flows'
    
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False)
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    operational_cash_flow = Column(Float, default=0)
    investment_cash_flow = Column(Float, default=0)
    financing_cash_flow = Column(Float, default=0)
    
    # Relationship
    company = relationship("Company", back_populates="cash_flows")

class KPI(Base):
    __tablename__ = 'kpis'
    
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False)
    year = Column(Integer, nullable=False)
    cac = Column(Float, default=0)  # Customer Acquisition Cost
    ltv = Column(Float, default=0)  # Lifetime Value
    burn_rate = Column(Float, default=0)
    revenue_growth = Column(Float, default=0.1)
    expense_growth = Column(Float, default=0.08)
    projection_years = Column(Integer, default=3)
    
    # Relationship
    company = relationship("Company", back_populates="kpis")

class FinancialNote(Base):
    __tablename__ = 'financial_notes'
    
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False)
    year = Column(Integer, nullable=False)
    growth_strategy = Column(String)
    business_risks = Column(String)
    anomalies = Column(String)
    funding_requirements = Column(Float, default=0)
    funding_allocation = Column(String)
    
    # Relationship
    company = relationship("Company", back_populates="financial_notes")

# Buat tabel di database jika belum ada
Base.metadata.create_all(engine)

# Buat sessionmaker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Function untuk mendapatkan session database
def get_db_session():
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()

# Function untuk menyimpan data ke database
def save_financial_data(company_id, year, month, revenue, cogs, op_expenses, other_expenses, tax_rate=0.2):
    db = get_db_session()
    
    # Cek apakah data sudah ada untuk bulan dan tahun tertentu
    existing_data = db.query(FinancialData).filter(
        FinancialData.company_id == company_id,
        FinancialData.year == year,
        FinancialData.month == month
    ).first()
    
    if existing_data:
        # Update data yang sudah ada
        existing_data.revenue = revenue
        existing_data.cogs = cogs
        existing_data.operational_expenses = op_expenses
        existing_data.other_expenses = other_expenses
        existing_data.tax_rate = tax_rate
    else:
        # Buat data baru
        new_data = FinancialData(
            company_id=company_id,
            year=year,
            month=month,
            revenue=revenue,
            cogs=cogs,
            operational_expenses=op_expenses,
            other_expenses=other_expenses,
            tax_rate=tax_rate
        )
        db.add(new_data)
    
    db.commit()

def save_balance_sheet(company_id, year, current_assets, fixed_assets, short_term_liabilities, 
                      long_term_liabilities, owner_equity, retained_earnings):
    db = get_db_session()
    
    # Cek apakah balance sheet sudah ada untuk tahun tertentu
    existing_data = db.query(BalanceSheet).filter(
        BalanceSheet.company_id == company_id,
        BalanceSheet.year == year
    ).first()
    
    if existing_data:
        # Update data yang sudah ada
        existing_data.current_assets = current_assets
        existing_data.fixed_assets = fixed_assets
        existing_data.short_term_liabilities = short_term_liabilities
        existing_data.long_term_liabilities = long_term_liabilities
        existing_data.owner_equity = owner_equity
        existing_data.retained_earnings = retained_earnings
    else:
        # Buat data baru
        new_data = BalanceSheet(
            company_id=company_id,
            year=year,
            current_assets=current_assets,
            fixed_assets=fixed_assets,
            short_term_liabilities=short_term_liabilities,
            long_term_liabilities=long_term_liabilities,
            owner_equity=owner_equity,
            retained_earnings=retained_earnings
        )
        db.add(new_data)
    
    db.commit()

def save_cash_flow(company_id, year, month, operational_cash_flow, investment_cash_flow, financing_cash_flow):
    db = get_db_session()
    
    # Cek apakah data sudah ada untuk bulan dan tahun tertentu
    existing_data = db.query(CashFlow).filter(
        CashFlow.company_id == company_id,
        CashFlow.year == year,
        CashFlow.month == month
    ).first()
    
    if existing_data:
        # Update data yang sudah ada
        existing_data.operational_cash_flow = operational_cash_flow
        existing_data.investment_cash_flow = investment_cash_flow
        existing_data.financing_cash_flow = financing_cash_flow
    else:
        # Buat data baru
        new_data = CashFlow(
            company_id=company_id,
            year=year,
            month=month,
            operational_cash_flow=operational_cash_flow,
            investment_cash_flow=investment_cash_flow,
            financing_cash_flow=financing_cash_flow
        )
        db.add(new_data)
    
    db.commit()

def save_kpi(company_id, year, cac, ltv, burn_rate, revenue_growth=0.1, expense_growth=0.08, projection_years=3):
    db = get_db_session()
    
    # Cek apakah KPI sudah ada untuk tahun tertentu
    existing_data = db.query(KPI).filter(
        KPI.company_id == company_id,
        KPI.year == year
    ).first()
    
    if existing_data:
        # Update data yang sudah ada
        existing_data.cac = cac
        existing_data.ltv = ltv
        existing_data.burn_rate = burn_rate
        existing_data.revenue_growth = revenue_growth
        existing_data.expense_growth = expense_growth
        existing_data.projection_years = projection_years
    else:
        # Buat data baru
        new_data = KPI(
            company_id=company_id,
            year=year,
            cac=cac,
            ltv=ltv,
            burn_rate=burn_rate,
            revenue_growth=revenue_growth,
            expense_growth=expense_growth,
            projection_years=projection_years
        )
        db.add(new_data)
    
    db.commit()

def save_financial_note(company_id, year, growth_strategy, business_risks, anomalies, 
                        funding_requirements, funding_allocation):
    db = get_db_session()
    
    # Cek apakah financial note sudah ada untuk tahun tertentu
    existing_data = db.query(FinancialNote).filter(
        FinancialNote.company_id == company_id,
        FinancialNote.year == year
    ).first()
    
    if existing_data:
        # Update data yang sudah ada
        existing_data.growth_strategy = growth_strategy
        existing_data.business_risks = business_risks
        existing_data.anomalies = anomalies
        existing_data.funding_requirements = funding_requirements
        existing_data.funding_allocation = funding_allocation
    else:
        # Buat data baru
        new_data = FinancialNote(
            company_id=company_id,
            year=year,
            growth_strategy=growth_strategy,
            business_risks=business_risks,
            anomalies=anomalies,
            funding_requirements=funding_requirements,
            funding_allocation=funding_allocation
        )
        db.add(new_data)
    
    db.commit()

def create_company(name, industry=None, founded_date=None):
    db = get_db_session()
    
    new_company = Company(
        name=name,
        industry=industry,
        founded_date=founded_date
    )
    
    db.add(new_company)
    db.commit()
    db.refresh(new_company)
    
    return new_company.id

def get_companies():
    db = get_db_session()
    return db.query(Company).all()

def get_company_by_id(company_id):
    db = get_db_session()
    return db.query(Company).filter(Company.id == company_id).first()

def get_financial_data(company_id, year=None):
    db = get_db_session()
    query = db.query(FinancialData).filter(FinancialData.company_id == company_id)
    
    if year:
        query = query.filter(FinancialData.year == year)
    
    return query.all()

def get_balance_sheet(company_id, year=None):
    db = get_db_session()
    query = db.query(BalanceSheet).filter(BalanceSheet.company_id == company_id)
    
    if year:
        query = query.filter(BalanceSheet.year == year)
    
    return query.all()

def get_cash_flow(company_id, year=None):
    db = get_db_session()
    query = db.query(CashFlow).filter(CashFlow.company_id == company_id)
    
    if year:
        query = query.filter(CashFlow.year == year)
    
    return query.all()

def get_kpis(company_id, year=None):
    db = get_db_session()
    query = db.query(KPI).filter(KPI.company_id == company_id)
    
    if year:
        query = query.filter(KPI.year == year)
    
    return query.all()

def get_financial_notes(company_id, year=None):
    db = get_db_session()
    query = db.query(FinancialNote).filter(FinancialNote.company_id == company_id)
    
    if year:
        query = query.filter(FinancialNote.year == year)
    
    return query.all()

# Cek apakah sudah ada perusahaan di database, jika tidak buat perusahaan default
def init_db_with_default_data():
    db = get_db_session()
    
    # Cek apakah ada perusahaan
    companies = db.query(Company).all()
    
    if not companies:
        # Buat perusahaan default
        default_company = Company(
            name="PT Contoh Indonesia",
            industry="Teknologi",
            founded_date=datetime.date(2020, 1, 1)
        )
        
        db.add(default_company)
        db.commit()
        db.refresh(default_company)
        
        # Tambahkan beberapa data default
        current_year = datetime.datetime.now().year
        
        # Tambahkan data finansial untuk 12 bulan tahun ini
        for month in range(1, 13):
            new_data = FinancialData(
                company_id=default_company.id,
                year=current_year,
                month=month,
                revenue=1000000 * month,  # Hanya contoh data
                cogs=400000 * month,
                operational_expenses=200000 * month,
                other_expenses=50000 * month,
                tax_rate=0.2
            )
            db.add(new_data)
            
            # Tambahkan data arus kas untuk 12 bulan
            new_cash_flow = CashFlow(
                company_id=default_company.id,
                year=current_year,
                month=month,
                operational_cash_flow=300000 * month,
                investment_cash_flow=-100000 * month,
                financing_cash_flow=50000 * month
            )
            db.add(new_cash_flow)
        
        # Tambahkan balance sheet untuk tahun ini
        new_balance_sheet = BalanceSheet(
            company_id=default_company.id,
            year=current_year,
            current_assets=5000000,
            fixed_assets=10000000,
            short_term_liabilities=2000000,
            long_term_liabilities=5000000,
            owner_equity=6000000,
            retained_earnings=2000000
        )
        db.add(new_balance_sheet)
        
        # Tambahkan KPI untuk tahun ini
        new_kpi = KPI(
            company_id=default_company.id,
            year=current_year,
            cac=500000,
            ltv=2000000,
            burn_rate=3000000,
            revenue_growth=0.15,
            expense_growth=0.1,
            projection_years=3
        )
        db.add(new_kpi)
        
        # Tambahkan financial notes
        new_note = FinancialNote(
            company_id=default_company.id,
            year=current_year,
            growth_strategy="Mengembangkan produk baru dan ekspansi ke pasar Asia Tenggara",
            business_risks="Risiko regulasi dan kompetisi dari pemain besar",
            anomalies="Pertumbuhan pendapatan Q3 melambat karena pandemi",
            funding_requirements=10000000,
            funding_allocation="Pengembangan produk (40%), Pemasaran (30%), Operasional (20%), Cadangan (10%)"
        )
        db.add(new_note)
        
        db.commit()
        
        print(f"Database diinisialisasi dengan perusahaan default: {default_company.name}")
        return default_company.id
    
    return companies[0].id

# Jalankan inisialisasi database
default_company_id = init_db_with_default_data()