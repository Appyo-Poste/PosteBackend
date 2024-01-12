from django.shortcuts import render
from django.http import HttpResponse
from django.views.generic.list import ListView
from PosteAPI.models import Folder, User
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
