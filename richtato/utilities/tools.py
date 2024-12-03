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
        "255,215,0",  # Gold
        "220,20,60",  # Crimson
        "0,128,0",    # Dark Green
        "123,104,238",  # Medium Slate Blue
        "70,130,180",  # Steel Blue
        "255,140,0",  # Dark Orange
        "128,0,128",  # Purple
        "0,0,128",    # Navy
        "240,128,128",  # Light Coral
        "124,252,0",  # Lawn Green
        "176,224,230",  # Powder Blue
        "255,20,147",  # Deep Pink
        "255,105,180",  # Hot Pink
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

