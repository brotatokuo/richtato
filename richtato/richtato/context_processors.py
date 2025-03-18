from django.http import HttpRequest


def user_info(request: HttpRequest) -> dict:
    if request.user.is_authenticated:
        return {"username": request.user.username}
    return {}
