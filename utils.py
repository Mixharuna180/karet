def format_currency(value):
    """Format a number as currency with dollar sign and commas."""
    if not isinstance(value, (int, float)):
        return "$0.00"
    
    if value >= 0:
        return "${:,.2f}".format(value)
    else:
        # Handle negative values
        return "-${:,.2f}".format(abs(value))

def format_percentage(value, decimals=2):
    """Format a number as a percentage with specified decimal places."""
    if not isinstance(value, (int, float)):
        return "0.00%"
    
    return "{:.{}f}%".format(value * 100, decimals)
