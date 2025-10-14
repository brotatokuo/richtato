from datetime import datetime, timedelta

import pandas as pd
import plotly.graph_objects as go

from apps.account.models import Account
from apps.expense.models import Expense
from apps.income.models import Income
from categories.categories import BaseCategory


def get_category_icon(category_name: str) -> str:
    """Get the icon for a category by name."""
    try:
        # Get all registered categories
        categories = BaseCategory.get_registered_categories()

        # Find the category by name
        for category in categories:
            if category.name == category_name:
                return category.icon

        # Return default icon if category not found
        return "🛒"
    except Exception:
        # Return default icon if any error occurs
        return "🛒"


def get_category_color(category_name: str) -> str:
    """Get the color for a category by name."""
    try:
        # Get all registered categories
        categories = BaseCategory.get_registered_categories()

        # Find the category by name
        for category in categories:
            if category.name == category_name:
                return category.color

        # Return default color if category not found
        return "rgba(244, 67, 54, 0.6)"  # Default red
    except Exception:
        # Return default color if any error occurs
        return "rgba(244, 67, 54, 0.6)"  # Default red


def get_color_by_name(color_name: str) -> str:
    """Convert color name to rgba format."""
    color_map = {
        "red": "rgba(244, 67, 54, 0.6)",
        "blue": "rgba(33, 150, 243, 0.6)",
        "green": "rgba(76, 175, 80, 0.6)",
        "yellow": "rgba(255, 193, 7, 0.6)",
        "purple": "rgba(156, 39, 176, 0.6)",
        "orange": "rgba(255, 152, 0, 0.6)",
        "pink": "rgba(233, 30, 99, 0.6)",
        "brown": "rgba(121, 85, 72, 0.6)",
        "gray": "rgba(158, 158, 158, 0.6)",
    }
    return color_map.get(color_name.lower(), "rgba(244, 67, 54, 0.6)")


class SankeyDiagramBuilder:
    def __init__(self, df: pd.DataFrame, group_column: str, title: str | None = None):
        self.df = df
        self.group_column = group_column
        self.title = title
        self.source_label = "Expenses"

    def build(self) -> go.Figure:
        grouped = self.df.groupby(self.group_column)["amount"].sum().reset_index()

        # Add icons to labels if this is a category-based diagram
        if self.group_column == "category_name":
            labels = [self.source_label]
            for _, row in grouped.iterrows():
                category_name = str(row[self.group_column])
                if (
                    category_name
                    and category_name.strip()
                    and category_name.lower() != "nan"
                ):
                    icon = get_category_icon(category_name)
                    labels.append(f"{icon} {category_name}")
                else:
                    labels.append("❓ Unknown")
        else:
            labels = [self.source_label] + grouped[self.group_column].tolist()

        source = [0] * len(grouped)
        target = list(range(1, len(labels)))
        values = grouped["amount"].tolist()

        # Generate unique colors for each category
        link_colors = []
        for i, value in enumerate(values):
            if self.group_column == "category_name":
                # Get the category name from the label (remove icon)
                category_label = labels[i + 1]  # +1 because labels[0] is "Expenses"
                category_name = (
                    category_label.split(" ", 1)[1]
                    if " " in category_label
                    else category_label
                )

                # Get the category color
                category_color = get_category_color(category_name)
                link_colors.append(get_color_by_name(category_color))
            else:
                # Modern color palette matching dashboard theme
                color_palette = [
                    "rgba(152, 204, 44, 0.8)",  # Primary green (--green-color)
                    "rgba(129, 175, 38, 0.8)",  # Darker green (--darker-green-color)
                    "rgba(0, 117, 255, 0.8)",  # Blue (--blue-color)
                    "rgba(245, 158, 11, 0.8)",  # Orange (--orange-color)
                    "rgba(99, 102, 241, 0.8)",  # Modern purple
                    "rgba(236, 72, 153, 0.8)",  # Modern pink
                    "rgba(6, 182, 212, 0.8)",  # Modern cyan
                    "rgba(251, 146, 60, 0.8)",  # Modern orange
                ]
                link_colors.append(color_palette[i % len(color_palette)])

        fig = go.Figure(
            go.Sankey(
                node=dict(
                    label=labels,
                    pad=15,  # Reduced padding to fit better
                    thickness=20,  # Reduced thickness for better fit
                    color="#2d2d2d",  # Match --primary-color from theme
                    line=dict(
                        color="#98cc2c", width=1.5
                    ),  # Green border matching theme
                ),
                link=dict(
                    source=source,
                    target=target,
                    value=values,
                    color=link_colors,
                    hoverlabel=dict(
                        bgcolor="#2d2d2d",
                        bordercolor="#98cc2c",
                        font=dict(color="#ffffff", family="Open Sans, sans-serif"),
                    ),
                ),
            )
        )

        fig.update_layout(
            title_text=self.title,
            title_font=dict(
                size=18, color="#ffffff", family="Open Sans, sans-serif", weight="bold"
            ),
            font=dict(size=13, color="#ffffff", family="Open Sans, sans-serif"),
            paper_bgcolor="rgba(0,0,0,0)",  # Transparent to match dashboard
            plot_bgcolor="rgba(0,0,0,0)",  # Transparent plot area
            autosize=True,
            margin=dict(l=10, r=10, t=30, b=10),  # Minimal margins to fit container
            height=350,  # Reduced height to fit better
            hoverlabel=dict(
                bgcolor="#2d2d2d",
                bordercolor="#98cc2c",
                font=dict(color="#ffffff", family="Open Sans, sans-serif"),
            ),
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
        Income.objects.filter(user_id=user_id, date__gte=start_date, date__lte=end_date)  # type: ignore
        .select_related("account_name")
        .values("description", "amount", "account_name__type")
    )

    # Get user's expense data
    expense_data = (
        Expense.objects.filter(  # type: ignore
            user_id=user_id, date__gte=start_date, date__lte=end_date
        )
        .select_related("category")
        .values("amount", "category__name")
    )

    # Get user's account balances to determine savings vs spending
    accounts = Account.objects.filter(user_id=user_id).values(  # type: ignore
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
        # Merge by both description and account type
        merged_income = (
            income_df.groupby(["description", "account_name__type"])
            .agg({"amount": "sum"})
            .reset_index()
        )

        # Add income source labels
        income_sources = merged_income["description"].unique().tolist()
        for source_name in income_sources:
            labels.append(f"💰 {source_name}")

        # Add account type labels
        account_types = merged_income["account_name__type"].unique().tolist()
        account_type_labels = []
        for acc_type in account_types:
            if acc_type == "savings":
                account_type_labels.append("🏦 Savings")
            elif acc_type == "investment":
                account_type_labels.append("📈 Investment")
            elif acc_type == "retirement":
                account_type_labels.append("🏛️ Retirement")
            else:
                account_type_labels.append(f"💳 {str(acc_type).title()}")

        labels.extend(account_type_labels)

        # Create flows from income sources to account types (merged)
        for _, row in merged_income.iterrows():
            source_idx = labels.index(f"💰 {row['description']}")

            # Find target account type
            if row["account_name__type"] == "savings":
                target_label = "🏦 Savings"
            elif row["account_name__type"] == "investment":
                target_label = "📈 Investment"
            elif row["account_name__type"] == "retirement":
                target_label = "🏛️ Retirement"
            else:
                target_label = f"💳 {str(row['account_name__type']).title()}"

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
                icon = get_category_icon(str(category))
                labels.append(f"{icon} {category}")

        # Estimate flows from account types to expenses
        # For simplicity, we'll assume expenses come proportionally from checking accounts
        # and some from savings if checking is insufficient

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
                        icon = get_category_icon(str(category))
                        category_label = f"{icon} {category}"
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
    link_colors = []

    # Get all category names to identify expense categories
    category_names = []
    categories = BaseCategory.get_registered_categories()
    # Exclude "savings" and "investments" as they are account types, not expense categories
    category_names = [
        category.name.lower()
        for category in categories
        if category.name.lower() not in ["savings", "investments"]
    ]

    for i, value in enumerate(values):
        # Color based on flow type
        source_label = labels[source[i]] if source else ""
        target_label = labels[target[i]] if target else ""

        # Check if target is an expense category (contains any category name)
        is_expense_category = any(
            category_name in target_label.lower() for category_name in category_names
        )

        if "💰" in source_label and "🏦" in target_label:
            # Income to savings - primary green
            link_colors.append("rgba(152, 204, 44, 0.8)")
        elif "💰" in source_label and "📈" in target_label:
            # Income to investment - theme blue
            link_colors.append("rgba(0, 117, 255, 0.8)")
        elif "💰" in source_label and "🏛️" in target_label:
            # Income to retirement - modern purple
            link_colors.append("rgba(99, 102, 241, 0.8)")
        elif "💰" in source_label and "💳" in target_label:
            # Income to checking - darker green
            link_colors.append("rgba(129, 175, 38, 0.8)")
        elif is_expense_category:
            # Get unique color for each expense category
            category_color = "rgba(244, 67, 54, 0.6)"  # Default red
            for category_name in category_names:
                if category_name in target_label.lower():
                    # Find the category and get its color
                    for category in categories:
                        if category.name.lower() == category_name:
                            category_color = get_color_by_name(category.color)
                            break
                    break
            link_colors.append(category_color)
        elif "🏦" in source_label or "savings" in source_label.lower():
            # Savings flows - modern green variant
            link_colors.append("rgba(34, 197, 94, 0.8)")
        elif "📈" in source_label or "investment" in source_label.lower():
            # Investment flows - modern cyan
            link_colors.append("rgba(6, 182, 212, 0.8)")
        elif "🏛️" in source_label or "retirement" in source_label.lower():
            # Retirement flows - modern indigo
            link_colors.append("rgba(79, 70, 229, 0.8)")
        else:
            # Default - primary theme green
            link_colors.append("rgba(152, 204, 44, 0.8)")

    # Create the figure with modern styling
    fig = go.Figure(
        go.Sankey(
            node=dict(
                label=labels,
                pad=15,  # Reduced padding for better container fit
                thickness=20,  # Reduced thickness
                color="#2d2d2d",  # Match --primary-color from theme
                line=dict(color="#98cc2c", width=1.5),  # Green border matching theme
            ),
            link=dict(
                source=source,
                target=target,
                value=values,
                color=link_colors,
                hoverlabel=dict(
                    bgcolor="#2d2d2d",
                    bordercolor="#98cc2c",
                    font=dict(color="#ffffff", family="Open Sans, sans-serif"),
                ),
            ),
        )
    )

    fig.update_layout(
        title_font=dict(
            size=20, color="#ffffff", family="Open Sans, sans-serif", weight="bold"
        ),
        font=dict(size=14, color="#ffffff", family="Open Sans, sans-serif"),
        paper_bgcolor="rgba(0,0,0,0)",  # Transparent to match dashboard background
        plot_bgcolor="rgba(0,0,0,0)",  # Transparent plot area
        autosize=True,
        margin=dict(l=20, r=20, t=40, b=20),  # Reduced margins to fit container
        hoverlabel=dict(
            bgcolor="#2d2d2d",
            bordercolor="#98cc2c",
            font=dict(color="#ffffff", family="Open Sans, sans-serif"),
        ),
    )

    return fig
