

class ChartTheme:
    def __init__(self) -> None:
        self.themes = {
            "vibrant": [
                "#FF6F61", "#6B5B95", "#88B04B", "#F7CAC9", "#92A8D1",
                "#955251", "#B565A7", "#009B77", "#DD4124", "#45B8AC",
                "#D65076", "#EFC050", "#5B5EA6", "#9B2335", "#DFCFBE",
                "#BC243C", "#C3447A", "#7FCDCD", "#92A8D1", "#B565A7"
            ],
            "neon": [
                "#FF5733", "#33FF57", "#3357FF", "#FF33D1", "#33FFF6",
                "#FF33A6", "#33FFD1", "#FF8C33", "#FF5733", "#FF33C8",
                "#57FF33", "#A633FF", "#FF3380", "#FFB833", "#33C2FF",
                "#FF3368", "#33FFCC", "#FFA633", "#33FF99", "#FF3366"
            ],
            "pastel": [
                "#A1D9FF", "#FFC1E3", "#C1FFD9", "#FFD7A1", "#FFFAA1",
                "#A1D9FF", "#FFC1FF", "#C1FFC1", "#FFB5B5", "#C1C1FF",
                "#FFD1A1", "#FF99A1", "#D9A1FF", "#FFC1A1", "#B5A1FF",
                "#A1B5FF", "#A1FFA1", "#FFA1D9", "#FFD1FF", "#A1FFB5"
            ],
            "retro": [
                "#F08080", "#FFD700", "#7FFFD4", "#FF69B4", "#FF4500",
                "#4682B4", "#D2691E", "#FFDAB9", "#6A5ACD", "#008080",
                "#C71585", "#FF6347", "#DB7093", "#B22222", "#7B68EE",
                "#20B2AA", "#FFDEAD", "#32CD32", "#BA55D3", "#EE82EE"
            ]
        }
    
    def get_theme(self, theme_name: str) -> list:
        """
        Get the color theme by its name. If the theme does not exist,
        return the default 'vibrant' theme.
        """
        return self.themes.get(theme_name, self.themes["vibrant"])