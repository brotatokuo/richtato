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

        # Assign distinct colors for each target link
        color_palette = [
            "#4e79a7",
            "#f28e2b",
            "#e15759",
            "#76b7b2",
            "#59a14f",
            "#edc949",
            "#af7aa1",
            "#ff9da7",
            "#9c755f",
            "#bab0ab",
        ]
        link_colors = [
            color_palette[i % len(color_palette)] for i in range(len(values))
        ]

        fig = go.Figure(
            go.Sankey(
                node=dict(
                    label=labels,
                    pad=15,
                    thickness=20,
                    color="#CCCCCC",  # light gray node boxes
                    line=dict(color="#888888", width=0.5),
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
            font=dict(size=12, color="#EDEDED"),
            paper_bgcolor="#2b2b2b",  # dark grey background
            plot_bgcolor="#2b2b2b",
            autosize=True,
        )

        return fig


def sankey_by_account(df) -> go.Figure:
    return SankeyDiagramBuilder(df, group_column="account_name").build()


def sankey_by_category(df) -> go.Figure:
    return SankeyDiagramBuilder(df, group_column="category_name").build()


def convert_plotly_fig_to_html(fig) -> str:
    """
    Convert a Plotly figure to HTML.
    """
    return pio.to_html(
        fig,
        full_html=False,
        include_plotlyjs="cdn",
        config={"responsive": True},
    )
