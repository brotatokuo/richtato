# views/auth_views.py
import os

from apps.richtato_user.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import HttpRequest, HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.views import View
from loguru import logger


def index(request: HttpRequest) -> HttpResponseRedirect:
    if request.user.is_authenticated:
        logger.debug(f"User {request.user} is authenticated.")
        return HttpResponseRedirect(reverse("dashboard"))
    else:
        return HttpResponseRedirect(reverse("welcome"))


def dashboard(request: HttpRequest):
    deploy_stage = os.getenv("DEPLOY_STAGE")
    if deploy_stage and deploy_stage.upper() == "PROD":
        suffix = ""
    else:
        suffix = deploy_stage
    return render(request, "dashboard.html", {"suffix": suffix})


def welcome(request: HttpRequest):
    return render(request, "welcome.html")


@login_required
def get_user_id(request: HttpRequest):
    return JsonResponse({"userID": request.user.pk})


def friends(request: HttpRequest):
    return render(request, "friends.html")


def files(request: HttpRequest):
    return render(request, "files.html")


def goals(request: HttpRequest):
    return render(request, "goals.html")


def profile(request: HttpRequest):
    return render(request, "profile.html")


class LoginView(View):
    def get(self, request: HttpRequest):
        return render(
            request,
            "login.html",
            {
                "username": "",
                "message": None,
                "deploy_stage": os.getenv("DEPLOY_STAGE"),
            },
        )

    def post(self, request: HttpRequest):
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(
                request,
                "login.html",
                {
                    "username": username,
                    "message": "Invalid username and/or password.",
                    "deploy_stage": os.getenv("DEPLOY_STAGE"),
                },
            )


class LogoutView(View):
    def get(self, request: HttpRequest):
        logout(request)
        return HttpResponseRedirect(reverse("index"))


class RegisterView(View):
    def get(self, request: HttpRequest):
        return render(
            request, "register.html", {"deploy_stage": os.getenv("DEPLOY_STAGE")}
        )

    def post(self, request: HttpRequest):
        username = request.POST.get("username")
        password = request.POST.get("password")
        confirmation = request.POST.get("password2")

        if password != confirmation:
            return render(
                request,
                "register.html",
                {
                    "message": "Passwords must match.",
                    "deploy_stage": os.getenv("DEPLOY_STAGE"),
                },
            )

        try:
            user = User.objects.create_user(username=username, password=password)
            user.save()

        except IntegrityError:
            return render(
                request, "register.html", {"message": "Username already taken."}
            )

        login(request, user)
        return HttpResponseRedirect(reverse("index"))
