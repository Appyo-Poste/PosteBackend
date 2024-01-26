from django.contrib.auth import login, authenticate, logout
from django.db.models import Q

from django.shortcuts import render
from django.http import HttpResponse
from django.views.generic.list import ListView
from PosteAPI.models import Folder, User, FolderPermissionEnum
from PosteWeb.forms import LoginForm, RegisterForm
from django.shortcuts import redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django.urls import reverse_lazy
from django.views import generic
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin

User = get_user_model()

import pprint

pp = pprint.PrettyPrinter(indent=4)


# Create your views here.
def index(request):
    return HttpResponse("This is the poste index.")


"""
Shows a simple list of of folders filter by creator.
"""


class folderPage(LoginRequiredMixin, ListView):
    login_url = "/poste/login/"
    model = Folder
    template_name = "folder_list.html"

    def get_queryset(self, **kwargs):
        user = self.request.user
        qs = super().get_queryset(**kwargs)
        qs = qs.filter(Q(creator=user)
                       | Q(
            folderpermission__user=user,
            folderpermission__permission__in=[
                FolderPermissionEnum.FULL_ACCESS,
                FolderPermissionEnum.EDITOR,
                FolderPermissionEnum.VIEWER,
            ],
        )
                       ).distinct()
        return qs


"""
Tests and demostars a way to check if a user is longed in or not. 
All view will have login checking are redirect to the login screen.
actually site will likely use @login_required instead.
"""


def checkLogin(request):
    if not request.user.is_authenticated:
        return HttpResponse("you are not loged in.")
    else:
        return HttpResponse("you are loged in.")


def login_page(request):
    form = LoginForm()
    message = ''
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user = authenticate(
                username=form.data['username'],
                password=form.cleaned_data['password']
            )
        if user is not None:
            login(request, user)
            message = f'Hello {user.username}! You have been logged in'
            return redirect("folders")
        else:
            message = "login failed"
    return render(request, 'Login.html', context={'form': form, 'message': message})


def landing_page(request):
    return render(request, 'landing_page.html')


def sign_up(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect("login")

    else:
        form = RegisterForm()

    return render(request, 'sign_up.html', {'form': form})


@login_required(login_url="/poste/login/")
def setting(request):
    return render(request, 'setting.html')


def logout_page(request):
    logout(request)
    return render(request, 'logout.html')