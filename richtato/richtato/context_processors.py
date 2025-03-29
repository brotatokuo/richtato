from django.http import HttpRequest
from datetime import datetime

def user_info(request: HttpRequest) -> dict:
    if request.user.is_authenticated:
        return {"username": request.user.username}
    return {}

def date(request: HttpRequest) -> dict:
    current_date = datetime.now()
    return {
        "current_year": str(current_date.year),
        "current_month": str(current_date.strftime("%B")),
        "current_day": str(current_date.day),
    }