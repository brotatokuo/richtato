import plotly.graph_objects as go


def sankey_by_account(df) -> go.Figure:
    source_label = "Expenses"

    # Group amounts by account_name
    grouped = df.groupby("account_name")["amount"].sum().reset_index()

    labels = [source_label] + grouped["account_name"].tolist()
    source = [0] * len(grouped)  # from "Expenses" node
    target = list(range(1, len(labels)))  # to each account node
    values = grouped["amount"].tolist()

    fig = go.Figure(
        go.Sankey(
            node=dict(label=labels, pad=15, thickness=20),
            link=dict(source=source, target=target, value=values),
        )
    )

    fig.update_layout(title_text="Expenses split by Account Name", font_size=10)
    return fig


def sankey_by_category(df) -> go.Figure:
    source_label = "Expenses"
    # Group amounts by category_name
    grouped = df.groupby("category_name")["amount"].sum().reset_index()

    labels = [source_label] + grouped["category_name"].tolist()
    source = [0] * len(grouped)  # from "Expenses" node
    target = list(range(1, len(labels)))  # to each category node
    values = grouped["amount"].tolist()

    fig = go.Figure(
        go.Sankey(
            node=dict(label=labels, pad=15, thickness=20),
            link=dict(source=source, target=target, value=values),
        )
    )

    fig.update_layout(title_text="Expenses split by Category", font_size=10)
    return fig
