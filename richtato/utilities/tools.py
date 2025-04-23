def format_currency(value):
    if value < 0:
        return "-${:,.2f}".format(abs(value))
    return "${:,.2f}".format(value)


def format_date(value):
    return value.strftime("%Y-%m-%d")
