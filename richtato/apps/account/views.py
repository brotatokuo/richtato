import calendar
import json
import pandas as pd
from typing import Any
from datetime import datetime

from django.db.models import F, Value, CharField
from django.contrib.auth.decorators import login_required
from django.shortcuts import HttpResponse, render
from django.http import JsonResponse
from django.db.models.functions import Cast, TruncYear, TruncMonth, TruncDate

from apps.account.models import Account, AccountHistory
from utilities.tools import color_picker, month_mapping

@login_required
def account(request):
    accounts_data, unique_years = get_accounts_data(request)
    return render(
        request,
        "accounts.html",
        {
            "networth": request.user.networth(),
            "accounts_data": accounts_data,
            "years": unique_years,
            "today_date": datetime.today().strftime("%Y-%m-%d"),
        },
    )

@login_required
def add(request):
    if request.method == "POST":
        account_type = request.POST.get("account-type")
        account_name = request.POST.get("account-name")
        balance_date = request.POST.get("balance-date")
        balance = request.POST.get("balance-input")

        if Account.objects.filter(user=request.user, name=account_name).exists():
            return render(
                request,
                "settings.html",
                {
                    "error_account_message": "Account name already exists. Please choose a different name.",
                },
            )

        account = Account(
            user=request.user,
            type=account_type,
            name=account_name,
        )
        account.save()

        account_history = AccountHistory(
            account=account,
            balance_history=balance,
            date_history=balance_date,
        )
        account_history.save()

        return view(request)
    return HttpResponse("Add account error")

def get_accounts_data(request) -> tuple[list[dict[str, Any]], list[int]]:
    year = request.GET.get("year")
    label = request.GET.get("label")
    month = month_mapping(request.GET.get("month"))
    
    accounts_histories = (
    AccountHistory.objects.filter(account__user=request.user)
    .annotate(
        Year=TruncYear("date_history"),
        Month=TruncMonth("date_history"),
        Date=TruncDate("date_history"),
        Name=F("account__name"),
        Balance=Cast("balance_history", output_field=CharField()),
    )
    .filter(Year=year, Month=month, Name=label)
)
    accounts_data = list(accounts_histories.values())
    unique_years = list(accounts_histories.values_list('Year', flat=True).distinct().order_by('-Year'))
    return accounts_data, unique_years

@login_required
def add_account_history(request):
    if request.method == "POST":
        account = Account.objects.get(id=request.POST.get("account-id"))
        balance = request.POST.get("balance-input")
        date = request.POST.get("balance-date")

        account_history = AccountHistory(
            account=account,
            balance_history=balance,
            date_history=date,
        )
        account_history.save()
        return view(request)
    return HttpResponse("Add account history error")

@login_required
def update_accounts(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))

            for transaction_data in data:
                request_user = transaction_data.get("user")
                delete_bool = transaction_data.get("delete")
                transaction_id = transaction_data.get("id")
                account_name = transaction_data.get("name")
                date = transaction_data.get("date")
                amount = float(transaction_data.get("balance").replace("$", "").replace(",", ""))
                
                if delete_bool:
                    AccountHistory.objects.get(id=transaction_id).delete()
                    print("Account History Deleted: ", transaction_id)
                    continue

                AccountHistory.objects.update_or_create(
                    id=transaction_id,
                    defaults={
                        "date_history": date,
                        "balance_history": amount,
                        "account": Account.objects.get(user=request_user, name=account_name),
                    },
                )
            return JsonResponse({"success": True})

        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "error": "Invalid request"})

# @login_required
# def plot_accounts_data(request):
#     df = get_accounts_data_monthly_df(request)
#     df["YearMonth"] = df["Date"].dt.to_period("M")
#     df = df.sort_values("Date").drop_duplicates(
#         ["Account Name", "YearMonth"], keep="last"
#     )
#     df = df.drop(columns=["YearMonth"])
#     years = df["Date"].dt.year.unique()
#     json_data = []
#     for year in years:
#         df_year = df[df["Date"].dt.year == year]
#         # Generating Labels (Months)
#         labels = [calendar.month_abbr[i] for i in range(1, 13)]

#         # Get Unique Account Names
#         accounts_list = df_year["Account Name"].unique()

#         datasets = []
#         for i in range(len(accounts_list)):
#             df_account = df_year[df_year["Account Name"] == accounts_list[i]]
#             max_month = df_account["Month"].max()
#             all_months = pd.DataFrame({"Month": range(1, max_month + 1)})
#             # # Merge the DataFrame with the complete list of months and fill missing values with 0
#             df_complete = all_months.merge(df_account, on="Month", how="left").fillna(0)
#             monthly_list = df_complete["Balance"].tolist()

#             dataset = {
#                 "label": accounts_list[i],  # Dataset label
#                 "backgroundColor": color_picker(i)[0],  # Background color
#                 "borderColor": color_picker(i)[1],  # Border color
#                 "borderWidth": 1,
#                 "data": monthly_list,
#             }
#             datasets.append(dataset)

#         json_data.append(
#             {"year": int(year), "labels": labels[0:max_month], "data": datasets}
#         )

#     return JsonResponse(json_data, safe=False)


# @login_required
# def plot_accounts_data_pie(request):
#     accounts_list = list(Account.objects.filter(user=request.user))
#     accounts_names_list = [account.name for account in accounts_list]
#     data_list = []
#     background_color_list = []
#     border_color_list = []
#     for i, account in enumerate(accounts_list):
#         latest_balance = account.latest_balance
#         print(account, "Latest Balance: ", latest_balance)
#         data_list.append(account.latest_balance)
#         background_color_list.append(color_picker(i)[0])
#         border_color_list.append(color_picker(i)[1])

#         datasets = [
#             {
#                 "data": data_list,
#                 "backgroundColor": background_color_list,
#                 "borderColor": border_color_list,
#             }
#         ]

#     print("Datasets: ", datasets)

#     # Structure the final response
#     response_data = {"labels": accounts_names_list, "datasets": datasets}

#     # print("Response Data: ", response_data)
#     return JsonResponse(response_data, safe=False)
