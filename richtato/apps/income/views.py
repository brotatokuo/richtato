import json
from datetime import datetime

import pandas as pd
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import HttpResponse, HttpResponseRedirect, render
from django.urls import reverse

from apps.account.models import Account
from apps.income.models import Income
from utilities.tools import month_mapping
from utilities.utils import get_transaction_data


@login_required
def income(request):
    earnings_dates = (
        Income.objects.filter(user=request.user)
        .exclude(date__isnull=True)
        .values_list("date", flat=True)
        .distinct()
    )
    years_list = sorted(set(date.year for date in earnings_dates), reverse=True)
    account_names = Account.objects.filter(user=request.user)
    account_name_list = [account.name for account in account_names]
    entries = Income.objects.filter(user=request.user).order_by("-date")
    print("Incomes Dates: ", earnings_dates)
    print("Accounts: ", account_name_list)
    print("Incomes Entries: ", entries)
    return render(
        request,
        "income.html",
        {
            "years": years_list,
            "entries": entries,
            "accounts": account_name_list,
            "today_date": datetime.today().strftime("%Y-%m-%d"),
        },
    )


@login_required
def add_earning_entry(request):
    if request.method == "POST":
        # Get the form data
        description = request.POST.get("description")
        amount = request.POST.get("amount")
        date = request.POST.get("balance-date")
        account = request.POST.get("account")

        account_name = Account.objects.get(user=request.user, name=account)
        # Create and save the transaction
        transaction = Income(
            user=request.user,
            account_name=account_name,
            description=description,
            date=date,
            amount=amount,
        )
        transaction.save()
        return HttpResponseRedirect(reverse("view_earnings"))
    return HttpResponse("Data Entry Error")


# @login_required
# def plot_earnings_data(request, verbose=False):
#     return plot_data(
#         request, context="Incomes", group_by="Description", verbose=verbose
#     )


@login_required
def update_earnings(request):
    if request.method == "POST":
        try:
            print("Update Incomes Request: ")
            # Decode the JSON body from the request
            data = json.loads(request.body.decode("utf-8"))
            print("Update Incomes Data: ", data)

            for transaction_data in data:
                # Extract the fields for each transaction
                delete_bool = transaction_data.get("delete")
                transaction_id = transaction_data.get("id")
                account_name = transaction_data.get("name")
                date = transaction_data.get("date")
                amount = transaction_data.get("amount")
                amount = float(amount.replace("$", "").replace(",", ""))

                if delete_bool:
                    Income.objects.get(id=transaction_id).delete()
                    print("Income Deleted: ", transaction_id)
                    continue

                Income.objects.update_or_create(
                    user=request.user,
                    id=transaction_id,
                    defaults={
                        "date": date,
                        "amount": amount,
                    },
                )

                print(
                    "Expense Updated: ", transaction_id, date, account_name, amount
                )

            return JsonResponse({"success": True})

        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "error": "Invalid request"})


@login_required
def get_earnings_data_json(request):
    year = request.GET.get("year")
    label = request.GET.get("label")
    month_str = request.GET.get("month")
    month = month_mapping(month_str)

    # Fetch the transaction data based on the user's context
    df = get_transaction_data(request.user, context="Incomes")

    # Filter data by year, label (description), and month
    df_filtered = df[df["Year"] == int(year)]
    df_filtered = df_filtered[df_filtered["Description"] == label]
    df_filtered = df_filtered[df_filtered["Month"] == int(month)]

    # Print filtered data for debugging
    print("Filtered Incomes Data: ", df_filtered)

    # Convert Date to 'YYYY-MM-DD' format and Balance to currency format
    df_filtered["Date"] = pd.to_datetime(df_filtered["Date"]).dt.strftime("%Y-%m-%d")
    df_filtered["Amount"] = df_filtered["Amount"].apply(
        lambda x: f"${x:,.2f}"
    )  # Format to 2 decimal places with currency symbol

    # Rename columns for JSON response
    df_filtered = df_filtered.rename(
        columns={"Account Name": "Name", "Date": "Date", "id": "Id"}
    )

    json_data = df_filtered[["Id", "Date", "Name", "Amount"]].to_dict(orient="records")

    # Return JSON response
    return JsonResponse(json_data, safe=False)


# @login_required
# def import_earnings_from_csv(request):
#     assert "DO NOT USE THIS FUNCTION" == "This function is for testing purposes only"
#     print("Importing Incomes from CSV")
#     csv_file = "viz/static/historic_data/tep_earning_20241110.csv"
#     if request.method == 'GET':
#         try:
#             df = pd.read_csv(csv_file)
#             print("CSV Data: ", df.head())
#             for index, row in df.iterrows():
#                 description = row['description']
#                 amount = row['amount']
#                 date = pd.to_datetime(row['date']).strftime('%Y-%m-%d')
#                 account_name = row['account_name']
#                 account = Account.objects.get(user=request.user, name=account_name)
#                 # Create and save the transaction
#                 transaction = Income(
#                     user=request.user,
#                     account_name = account,
#                     description=description,
#                     date=date,
#                     amount=amount,
#                 )
#                 transaction.save()
#             return HttpResponseRedirect(reverse("view_earnings"))
#         except Exception as e:
#             print("Error while importing earnings: ", e)
#             return HttpResponse("Error while importing earnings")
#     return HttpResponse("Invalid request")
