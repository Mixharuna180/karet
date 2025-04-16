def calculate_gross_margin(revenue, cogs):
    """
    Calculate gross margin percentage
    
    Gross Margin = (Revenue - COGS) / Revenue
    """
    if revenue == 0:
        return 0
    
    return (revenue - cogs) / revenue

def calculate_net_profit_margin(net_profit, revenue):
    """
    Calculate net profit margin percentage
    
    Net Profit Margin = Net Profit / Revenue
    """
    if revenue == 0:
        return 0
    
    return net_profit / revenue

def calculate_current_ratio(current_assets, current_liabilities):
    """
    Calculate current ratio
    
    Current Ratio = Current Assets / Current Liabilities
    """
    if current_liabilities == 0:
        return 0 if current_assets == 0 else float('inf')
    
    return current_assets / current_liabilities

def calculate_debt_to_equity(total_debt, total_equity):
    """
    Calculate debt-to-equity ratio
    
    Debt-to-Equity Ratio = Total Debt / Total Equity
    """
    if total_equity == 0:
        return float('inf') if total_debt > 0 else 0
    
    return total_debt / total_equity

def calculate_burn_rate(cash_balance, monthly_expenses, monthly_revenue):
    """
    Calculate burn rate (negative cash flow rate)
    
    Burn Rate = (Cash Balance) / (Monthly Expenses - Monthly Revenue)
    Returns the number of months until cash runs out
    """
    net_burn = monthly_expenses - monthly_revenue
    
    if net_burn <= 0:  # Company is profitable, no burn
        return 0
    
    if cash_balance <= 0:
        return 0  # Already out of cash
    
    return cash_balance / net_burn

def calculate_ltv_cac_ratio(ltv, cac):
    """
    Calculate LTV to CAC ratio
    
    LTV:CAC Ratio = LTV / CAC
    """
    if cac == 0:
        return 0
    
    return ltv / cac

def calculate_break_even_point(fixed_costs, contribution_margin_ratio):
    """
    Calculate break-even point in revenue
    
    Break-even Revenue = Fixed Costs / Contribution Margin Ratio
    """
    if contribution_margin_ratio == 0:
        return float('inf')
    
    return fixed_costs / contribution_margin_ratio

def calculate_working_capital(current_assets, current_liabilities):
    """
    Calculate working capital
    
    Working Capital = Current Assets - Current Liabilities
    """
    return current_assets - current_liabilities

def calculate_roi(net_profit, investment):
    """
    Calculate Return on Investment (ROI)
    
    ROI = Net Profit / Investment
    """
    if investment == 0:
        return 0
    
    return net_profit / investment
