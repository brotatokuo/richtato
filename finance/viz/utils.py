import pandas as pd
import os, warnings, calendar
from datetime import datetime
from django.http import HttpResponse, JsonResponse
from viz.models import *
from django.contrib.auth.decorators import login_required

warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")


@login_required
def get_latest_accounts_data(request) -> JsonResponse:
    user_accounts = request.user.account.all()
    user_accounts = sorted(user_accounts, key=lambda x: x.name)
    json_data = []
    for account in user_accounts:
        # Get the latest balance history record for the account
        balance_history = account.history.all()
        balance_list = []
        date_list = []

        for history in balance_history:
            balance_list.append(history.balance_history)  # Add balance to list
            date_list.append(history.date_history)  # Add date to list

        # Zip the balance and date lists together, then sort by the date
        sorted_history = sorted(
            zip(date_list, balance_list), key=lambda x: x[0], reverse=True
        )

        # Unzip the sorted result back into separate lists (if you need them)
        date_list_sorted, balance_list_sorted = (
            zip(*sorted_history) if sorted_history else ([], [])
        )

        # Get the latest balance and date
        latest_date = date_list_sorted[0] if date_list_sorted else None
        latest_balance = balance_list_sorted[0] if balance_list_sorted else None

        # Get account id
        account_id = account.id

        # Get account type
        account_type = account.type

        # Collect the necessary data for each account
        accounts_data = {
            "id": account_id,
            "account": account,
            "type": account_type,
            "balance": latest_balance,
            "date": latest_date,
            "history": list(zip(balance_list, date_list)),
        }
        json_data.append({"account_name": account.name, "accounts_data": accounts_data})
    return json_data


@login_required
def plot_data(request, context, group_by, verbose=False) -> JsonResponse:
    df = get_transaction_data(request.user, context=context)
    if df.empty:
        print(
            "\033[91mviews.py - _plot_data: No data available. Please import data first.\033[0m"
        )
    else:
        datasets = []
        # Split by Year
        year_list = df["Year"].unique()
        for year in year_list:
            df_year = df[df["Year"] == year]
            # Generating Labels (Months)
            labels = [calendar.month_abbr[i] for i in range(1, 13)]
            # Get Unique Account Names
            group_list = df_year[group_by].unique()
            # print("Unique Accounts: ", group_list)
            year_dataset_list = []
            for i in range(len(group_list)):
                df_account = df_year[df_year[group_by] == group_list[i]]
                df_monthly_sum = (
                    df_account.groupby("Month")["Amount"].sum().reset_index()
                )
                max_month = df_monthly_sum["Month"].max()
                all_months = pd.DataFrame({"Month": range(1, max_month + 1)})
                df_complete = all_months.merge(
                    df_monthly_sum, on="Month", how="left"
                ).fillna(0)
                monthly_spending_sum_list = df_complete["Amount"].tolist()

                year_dataset = {
                    "label": group_list[i],  # Dataset label
                    "backgroundColor": color_picker(i)[0],  # Background color
                    "borderColor": color_picker(i)[1],  # Border color
                    "borderWidth": 1,
                    "data": monthly_spending_sum_list,
                }
                year_dataset_list.append(year_dataset)
            datasets.append(
                {
                    "year": int(year),
                    "labels": labels[0:max_month],
                    "data": year_dataset_list,
                }
            )
        if verbose:
            print("Plot Data - Datasets: ", datasets)
        return JsonResponse(datasets, safe=False)


def get_transaction_data(user, context="Spendings", verbose=True) -> pd.DataFrame:
    """
    Get the transaction data from the SQL database
    """
    if context == "Spendings":
        dict = (
            Transaction.objects.filter(user=user)
            .select_related("account_name", "category")
            .values(
                "id",
                "date",
                "amount",
                "account_name__name",
                "category__name",
                "description",
            )
        )
        df = pd.DataFrame(list(dict))
    else:
        context = "Earnings"
        dict = (
            Earning.objects.filter(user=user)
            .select_related("account_name")
            .values("id", "date", "amount", "account_name__name", "description")
        )
        df = pd.DataFrame(list(dict))
    if verbose:
        print("User Accounts Dataframe:", dict)
        print("User Transactions Dataframe:", df)

    if df.empty:
        print("No data found in the database. Import data first.")
        return df
    else:
        df = _clean_db_df(df, context=context, verbose=False)
        # Convert Year Month Day to int
        df["id"] = df["id"].astype(int)
        df["Year"] = df["Year"].astype(int)
        df["Month"] = df["Month"].astype(int)
        df["Day"] = df["Day"].astype(int)
        return df


def get_accounts_data_monthly_df(request):
    users_accounts = Account.objects.filter(user=request.user)
    master_df = pd.DataFrame()
    for account in users_accounts:
        df = pd.DataFrame()

        balance_history = account.history.all()
        balance_history_df = pd.DataFrame(balance_history.values())
        print("Balance History DF:", balance_history_df)
        if not balance_history_df.empty:
            df["Date"] = pd.to_datetime(balance_history_df["date_history"])
            df["Balance"] = balance_history_df["balance_history"]
            df["Account Name"] = account.name
        master_df = pd.concat([master_df, df])

    # Organizing the data
    master_df["Month"] = master_df["Date"].dt.month
    return master_df


def _clean_db_df(df, context, verbose):
    if verbose:
        print("Structure SQL Data")
        print(df.head())

    # Organize Columns
    if context == "Spendings":
        df = df.rename(
            columns={
                "date": "Date",
                "account_name__name": "Account Name",
                "description": "Description",
                "amount": "Amount",
                "category__name": "Category",
            }
        )
        df = df[["id", "Date", "Account Name", "Description", "Amount", "Category"]]
    else:
        df = df.rename(
            columns={
                "date": "Date",
                "account_name__name": "Account Name",
                "description": "Description",
                "amount": "Amount",
            }
        )
        df = df[["id", "Date", "Account Name", "Description", "Amount"]]

    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce")
    df = df.sort_values(by="Date", ascending=True)

    if verbose:
        print("Renamed and Organized Columns")
        print(df.head())

    df = df[~df["Description"].str.contains("MOBILE PAYMENT", case=False, na=False)]
    df = df[~df["Description"].str.contains("ONLINE PAYMENT", case=False, na=False)]

    # Add Year, Month, Day
    df["Year"] = df["Date"].dt.year
    df["Month"] = df["Date"].dt.month
    df["Day"] = df["Date"].dt.day
    df["Date"] = pd.to_datetime(df["Date"], format="%m/%d/%Y").dt.date

    if verbose:
        print("Structured Transactions Data")
        print(df.head())
    return df
