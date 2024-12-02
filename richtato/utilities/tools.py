def color_picker(i):
    # Preset colors
    colors = [
        "152,204,44",  # Green
        "255,99,132",  # Red
        "54,162,235",  # Blue
        "255,159,64",  # Orange
        "153,102,255",  # Purple
        "255,206,86",  # Yellow
        "75,192,192",  # Teal
        "255,99,177",  # Pink
        "0,255,255",  # Cyan
        "54,54,235",  # Dark Blue
    ]

    if i + 1 > len(colors):
        color = "0,0,0"  # black
    else:
        color = colors[i]

    background_color = f"rgba({color}, 0.4)"
    border_color = f"rgba({color}, 1)"
    return background_color, border_color


def month_mapping(month):
    if isinstance(month, int):
        return month
    elif isinstance(month, str):
        month = month[:3]
        month_mapping = {
            "Jan": 1,
            "Feb": 2,
            "Mar": 3,
            "Apr": 4,
            "May": 5,
            "Jun": 6,
            "Jul": 7,
            "Aug": 8,
            "Sep": 9,
            "Oct": 10,
            "Nov": 11,
            "Dec": 12,
        }

        month = month_mapping[month]
    return month

def format_currency(value):
    return "${:,.2f}".format(value)

def format_date(value):
    return value.strftime("%Y-%m-%d")

