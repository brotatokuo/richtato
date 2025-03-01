# views/auth_views.py
from apps.richtato_user.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.views import View


@login_required
def get_user_id(request):
    return JsonResponse({"userID": request.user.id})


class IndexView(View):
    def get(self, request):
        return render(request, "index.html")


class LoginView(View):
    def get(self, request):
        return render(request, "login.html", {"username": "", "message": None})

    def post(self, request):
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(
                request,
                "login.html",
                {"username": username, "message": "Invalid username and/or password."},
            )


class LogoutView(View):
    def get(self, request):
        logout(request)
        return HttpResponseRedirect(reverse("index"))


class RegisterView(View):
    def get(self, request):
        return render(request, "register.html")

    def post(self, request):
        username = request.POST["username"]
        password = request.POST["password"]
        confirmation = request.POST["password2"]

        if password != confirmation:
            return render(
                request, "register.html", {"message": "Passwords must match."}
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
