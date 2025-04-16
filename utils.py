def format_currency(value):
    """Format a number as currency with Rupiah sign and commas."""
    if not isinstance(value, (int, float)):
        return "Rp0"
    
    if value >= 0:
        return "Rp{:,.0f}".format(value)
    else:
        # Handle negative values
        return "-Rp{:,.0f}".format(abs(value))

def format_percentage(value, decimals=2):
    """Format a number as a percentage with specified decimal places."""
    if not isinstance(value, (int, float)):
        return "0,00%"
    
    # Replace dot with comma for Indonesian format
    return "{:.{}f}%".format(value * 100, decimals).replace('.', ',')
