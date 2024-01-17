from django.contrib.auth import login, authenticate


from django.shortcuts import render
from django.http import HttpResponse
from django.views.generic.list import ListView
from PosteAPI.models import Folder, User
from PosteWeb.forms import LoginForm

import pprint
# Create your views here.
def index(request):
    return HttpResponse("This is the poste index.")

"""
Shows a simple list of of folders filter by creator.
"""
class folderPage(ListView):
    model = Folder

    def get_queryset(self, **kwargs):
        user = User.objects.get(email="atreichl@asu.edu")
        qs = super().get_queryset(**kwargs)
        return qs.filter(creator=user)

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
        form  = LoginForm(request.POST)
        if form.is_valid():
            user = authenticate(
                username=form.data['username'],
                password=form.cleaned_data['password']
            )
        if user is not None:
            login(request, user)
            message = f'Hello {user.username}! You have been logged in'
        else:
            message = "login failed"
    return render(request,'Login.html', context={'form': form, 'message': message})
