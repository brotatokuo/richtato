from datetime import datetime, timedelta

import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio

from richtato.apps.account.models import Account
from richtato.apps.expense.models import Expense
from richtato.apps.income.models import Income


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


def sankey_cash_flow_overview(user_id: int) -> go.Figure:
    """
    Create a comprehensive cash flow Sankey diagram showing:
    - Income sources (by description) flowing to account types
    - Account types flowing to expense categories
    - Show both raw values and percentages
    """
    # Get data for the last 6 months
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=180)

    # Get user's income data
    income_data = (
        Income.objects.filter(user_id=user_id, date__gte=start_date, date__lte=end_date)
        .select_related("account_name")
        .values("description", "amount", "account_name__type")
    )

    # Get user's expense data
    expense_data = (
        Expense.objects.filter(
            user_id=user_id, date__gte=start_date, date__lte=end_date
        )
        .select_related("category")
        .values("amount", "category__name")
    )

    # Get user's account balances to determine savings vs spending
    accounts = Account.objects.filter(user_id=user_id).values(
        "type", "latest_balance", "name"
    )

    # Build the Sankey diagram data
    labels = []
    source = []
    target = []
    values = []

    # Step 1: Income sources to account types
    income_df = pd.DataFrame(income_data)
    if not income_df.empty:
        income_totals = income_df.groupby("description")["amount"].sum()
        account_type_totals = income_df.groupby("account_name__type")["amount"].sum()

        # Add income source labels
        income_sources = income_totals.index.tolist()
        for source_name in income_sources:
            labels.append(f"💰 {source_name}")

        # Add account type labels
        account_types = account_type_totals.index.tolist()
        account_type_labels = []
        for acc_type in account_types:
            if acc_type == "savings":
                account_type_labels.append("🏦 Savings")
            elif acc_type == "investment":
                account_type_labels.append("📈 Investment")
            elif acc_type == "retirement":
                account_type_labels.append("🏛️ Retirement")
            else:
                account_type_labels.append(f"💳 {acc_type.title()}")

        labels.extend(account_type_labels)

        # Create flows from income sources to account types
        for _, row in income_df.iterrows():
            source_idx = labels.index(f"💰 {row['description']}")

            # Find target account type
            target_label = None
            if row["account_name__type"] == "savings":
                target_label = "🏦 Savings"
            elif row["account_name__type"] == "investment":
                target_label = "📈 Investment"
            elif row["account_name__type"] == "retirement":
                target_label = "🏛️ Retirement"
            else:
                target_label = f"💳 {row['account_name__type'].title()}"

            target_idx = labels.index(target_label)

            source.append(source_idx)
            target.append(target_idx)
            values.append(float(row["amount"]))

    # Step 2: Account types to expense categories
    expense_df = pd.DataFrame(expense_data)
    if not expense_df.empty:
        expense_totals = expense_df.groupby("category__name")["amount"].sum()

        # Add expense category labels
        expense_categories = expense_totals.index.tolist()
        for category in expense_categories:
            if category:
                labels.append(f"🛒 {category}")

        # Estimate flows from account types to expenses
        # For simplicity, we'll assume expenses come proportionally from checking accounts
        # and some from savings if checking is insufficient
        total_expenses = expense_df["amount"].sum()

        # Get checking account balance to determine flow
        checking_accounts = [acc for acc in accounts if acc["type"] == "checking"]
        total_checking = sum(
            acc["latest_balance"] for acc in checking_accounts if acc["latest_balance"]
        )

        # Create flows from account types to expense categories
        if total_checking > 0:
            checking_label = "💳 Checking"
            if checking_label in labels:
                checking_idx = labels.index(checking_label)

                for category, amount in expense_totals.items():
                    if category:
                        category_label = f"🛒 {category}"
                        if category_label in labels:
                            category_idx = labels.index(category_label)
                            source.append(checking_idx)
                            target.append(category_idx)
                            values.append(float(amount))

    # Step 3: Add savings and investment flows (showing money staying in accounts)
    savings_accounts = [acc for acc in accounts if acc["type"] == "savings"]
    investment_accounts = [acc for acc in accounts if acc["type"] == "investment"]
    retirement_accounts = [acc for acc in accounts if acc["type"] == "retirement"]

    # Add individual account labels for savings
    for acc in savings_accounts:
        if acc["name"]:
            labels.append(f"💰 {acc['name']}")

    # Add individual account labels for investments
    for acc in investment_accounts:
        if acc["name"]:
            labels.append(f"📊 {acc['name']}")

    # Add individual account labels for retirement
    for acc in retirement_accounts:
        if acc["name"]:
            labels.append(f"🏛️ {acc['name']}")

    # Create flows from account types to specific accounts
    savings_label = "🏦 Savings"
    if savings_label in labels:
        savings_idx = labels.index(savings_label)
        for acc in savings_accounts:
            if acc["name"] and acc["latest_balance"]:
                acc_label = f"💰 {acc['name']}"
                if acc_label in labels:
                    acc_idx = labels.index(acc_label)
                    source.append(savings_idx)
                    target.append(acc_idx)
                    values.append(
                        float(acc["latest_balance"]) * 0.1
                    )  # Show 10% of balance as flow

    investment_label = "📈 Investment"
    if investment_label in labels:
        investment_idx = labels.index(investment_label)
        for acc in investment_accounts:
            if acc["name"] and acc["latest_balance"]:
                acc_label = f"📊 {acc['name']}"
                if acc_label in labels:
                    acc_idx = labels.index(acc_label)
                    source.append(investment_idx)
                    target.append(acc_idx)
                    values.append(
                        float(acc["latest_balance"]) * 0.1
                    )  # Show 10% of balance as flow

    retirement_label = "🏛️ Retirement"
    if retirement_label in labels:
        retirement_idx = labels.index(retirement_label)
        for acc in retirement_accounts:
            if acc["name"] and acc["latest_balance"]:
                acc_label = f"🏛️ {acc['name']}"
                if acc_label in labels:
                    acc_idx = labels.index(acc_label)
                    source.append(retirement_idx)
                    target.append(acc_idx)
                    values.append(
                        float(acc["latest_balance"]) * 0.1
                    )  # Show 10% of balance as flow

    # Enhanced color palette for different flow types
    total_value = sum(values) if values else 1
    link_colors = []

    for i, value in enumerate(values):
        # Color based on flow type
        source_label = labels[source[i]] if source else ""
        target_label = labels[target[i]] if target else ""

        if "💰" in source_label and "🏦" in target_label:
            # Income to savings - green
            link_colors.append("rgba(76, 175, 80, 0.6)")
        elif "💰" in source_label and "📈" in target_label:
            # Income to investment - blue
            link_colors.append("rgba(33, 150, 243, 0.6)")
        elif "💰" in source_label and "🏛️" in target_label:
            # Income to retirement - purple
            link_colors.append("rgba(103, 58, 183, 0.6)")
        elif "💳" in source_label and "🛒" in target_label:
            # Checking to expenses - red
            link_colors.append("rgba(244, 67, 54, 0.6)")
        elif "🏦" in source_label:
            # Savings flows - light green
            link_colors.append("rgba(129, 199, 132, 0.6)")
        elif "📈" in source_label:
            # Investment flows - light blue
            link_colors.append("rgba(100, 181, 246, 0.6)")
        elif "🏛️" in source_label:
            # Retirement flows - light purple
            link_colors.append("rgba(149, 117, 205, 0.6)")
        else:
            # Default - primary green
            link_colors.append("rgba(152, 204, 44, 0.6)")

    # Create the figure
    fig = go.Figure(
        go.Sankey(
            node=dict(
                label=labels,
                pad=20,
                thickness=25,
                color="#4a5568",
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
        title_font=dict(size=16, color="#ffffff", family="Open Sans, sans-serif"),
        font=dict(size=12, color="#ffffff", family="Open Sans, sans-serif"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        autosize=True,
        margin=dict(l=20, r=20, t=60, b=20),
    )

    return fig
