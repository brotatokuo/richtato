def format_currency(value, decimals=2):
    format_str = f"{{:,.{decimals}f}}"
    if value < 0:
        return f"-${format_str.format(abs(value))}"
    return f"${format_str.format(value)}"


def format_date(value):
    return value.strftime("%Y-%m-%d")
