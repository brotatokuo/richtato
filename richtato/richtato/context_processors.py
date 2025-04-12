from datetime import datetime

from django.http import HttpRequest


def user_info(request: HttpRequest) -> dict:
    if request.user.is_authenticated:
        return {"username": request.user.username, "user_number": request.user.id}
    return {}


def date(request: HttpRequest) -> dict:
    current_date = datetime.now()
    return {
        "current_year": int(current_date.year),
        "current_month": str(current_date.strftime("%b")),
        "current_day": str(current_date.day),
        "today_date": str(current_date.strftime("%Y-%m-%d")),
    }
