import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio


class SankeyDiagramBuilder:
    def __init__(self, df: pd.DataFrame, group_column: str, title: str | None = None):
        self.df = df
        self.group_column = group_column
        self.title = title
        self.source_label = "Expenses"

    def build(self) -> go.Figure:
        grouped = self.df.groupby(self.group_column)["amount"].sum().reset_index()

        labels = [self.source_label] + grouped[self.group_column].tolist()
        source = [0] * len(grouped)
        target = list(range(1, len(labels)))
        values = grouped["amount"].tolist()

        # Modern color palette matching dashboard theme with transparency
        color_palette = [
            "rgba(152, 204, 44, 0.7)",  # Primary green
            "rgba(76, 175, 80, 0.7)",  # Green variant
            "rgba(129, 199, 132, 0.7)",  # Light green
            "rgba(165, 214, 167, 0.7)",  # Lighter green
            "rgba(200, 230, 201, 0.7)",  # Very light green
            "rgba(102, 187, 106, 0.7)",  # Medium green
            "rgba(139, 195, 74, 0.7)",  # Lime green
            "rgba(156, 204, 101, 0.7)",  # Light lime
            "rgba(220, 237, 200, 0.7)",  # Pale green
            "rgba(241, 248, 233, 0.7)",  # Very pale green
        ]
        link_colors = [
            color_palette[i % len(color_palette)] for i in range(len(values))
        ]

        fig = go.Figure(
            go.Sankey(
                node=dict(
                    label=labels,
                    pad=20,
                    thickness=25,
                    color="#4a5568",  # Dark gray matching dashboard
                    line=dict(color="#2d3748", width=1),
                ),
                link=dict(
                    source=source,
                    target=target,
                    value=values,
                    color=link_colors,
                ),
            )
        )

        fig.update_layout(
            title_text=self.title,
            title_font=dict(size=16, color="#ffffff", family="Open Sans, sans-serif"),
            font=dict(size=12, color="#ffffff", family="Open Sans, sans-serif"),
            paper_bgcolor="rgba(0,0,0,0)",  # Transparent background
            plot_bgcolor="rgba(0,0,0,0)",  # Transparent plot area
            autosize=True,
            margin=dict(l=20, r=20, t=40, b=20),
            height=350,
        )

        return fig


def sankey_by_account(df) -> go.Figure:
    return SankeyDiagramBuilder(df, group_column="account_name").build()


def sankey_by_category(df) -> go.Figure:
    return SankeyDiagramBuilder(df, group_column="category_name").build()


def convert_plotly_fig_to_html(fig) -> str:
    """
    Convert a Plotly figure to HTML with modern styling.
    """
    config = {
        "responsive": True,
        "displayModeBar": False,  # Hide the toolbar
        "staticPlot": False,
        "scrollZoom": False,  # Disable scroll zoom
        "doubleClick": False,  # Disable double click actions
        "showTips": False,  # Hide tips
        "displaylogo": False,  # Hide Plotly logo
    }

    html = pio.to_html(
        fig,
        full_html=False,
        include_plotlyjs="cdn",
        config=config,
        div_id=None,
    )

    # Add custom CSS to remove scrollbars and improve styling
    custom_css = """
    <style>
        .plotly-graph-div {
            overflow: hidden !important;
            border-radius: 8px;
        }
        .plotly-graph-div .svg-container {
            overflow: hidden !important;
        }
        .plotly-graph-div .main-svg {
            border-radius: 8px;
        }
        .js-plotly-plot .plotly .modebar {
            display: none !important;
        }
        .js-plotly-plot .plotly .modebar-group {
            display: none !important;
        }
    </style>
    """

    return custom_css + html
