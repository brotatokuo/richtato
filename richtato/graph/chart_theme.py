class ChartTheme:
    def __init__(self) -> None:
        self.themes = {
            "default": [
                "#98CC2C",  # Green
                "#FF6384",  # Red
                "#36A2EB",  # Blue
                "#FF9F40",  # Orange
                "#9966FF",  # Purple
                "#FFCE56",  # Yellow
                "#4BC0C0",  # Teal
                "#FF63B1",  # Pink
                "#00FFFF",  # Cyan
                "#3636EB",  # Dark Blue
                "#FFD700",  # Gold
                "#DC143C",  # Crimson
                "#008000",  # Dark Green
                "#7B68EE",  # Medium Slate Blue
                "#4682B4",  # Steel Blue
                "#FF8C00",  # Dark Orange
                "#800080",  # Purple
                "#000080",  # Navy
                "#F08080",  # Light Coral
                "#7CFC00",  # Lawn Green
                "#B0E0E6",  # Powder Blue
                "#FF1493",  # Deep Pink
                "#FF69B4",  # Hot Pink
            ],
            "pastel": [
                "#A1D9FF",
                "#FFC1E3",
                "#C1FFD9",
                "#FFD7A1",
                "#FFFAA1",
                "#A1D9FF",
                "#FFC1FF",
                "#C1FFC1",
                "#FFB5B5",
                "#C1C1FF",
                "#FFD1A1",
                "#FF99A1",
                "#D9A1FF",
                "#FFC1A1",
                "#B5A1FF",
                "#A1B5FF",
                "#A1FFA1",
                "#FFA1D9",
                "#FFD1FF",
                "#A1FFB5",
            ],
            "retro": [
                "#F08080",
                "#FFD700",
                "#7FFFD4",
                "#FF69B4",
                "#FF4500",
                "#4682B4",
                "#D2691E",
                "#FFDAB9",
                "#6A5ACD",
                "#008080",
                "#C71585",
                "#FF6347",
                "#DB7093",
                "#B22222",
                "#7B68EE",
                "#20B2AA",
                "#FFDEAD",
                "#32CD32",
                "#BA55D3",
                "#EE82EE",
            ],
        }

    def get_theme(self, theme_name: str) -> list:
        """
        Get the color theme by its name. If the theme does not exist,
        return the default 'vibrant' theme.
        """
        return self.themes.get(theme_name, self.themes["default"])
