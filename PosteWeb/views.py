from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.db.models import Q

from django.shortcuts import render
from django.http import HttpResponse, Http404
from django.views.generic.list import ListView
from django.views.generic.edit import DeleteView
from PosteAPI.models import Folder, User, FolderPermissionEnum, Post, Tag, FolderPermission
from PosteWeb.forms import LoginForm, RegisterForm, FolderCreate, PostCreate, FolderShare, ProfileEdit, \
    UpdatePasswordForm
from django.shortcuts import redirect
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import get_user_model, update_session_auth_hash
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


class folderPage(LoginRequiredMixin, ListView):
    login_url = "/poste/login/"
    model = Folder
    template_name = "folder_list.html"

    def get_context_data(self, **kwargs):
        context = super(folderPage, self).get_context_data(**kwargs)
        # adds the folder you are viewing as a context object that can be accessed in the html template
        context["root"] = Folder.objects.get(creator=self.request.user, is_root=True)
        return context

    def get_queryset(self, **kwargs):
        user = self.request.user
        root = Folder.objects.get(creator=user, is_root=True)
        qs = super().get_queryset(**kwargs)
        qs = qs.filter(Q(parent=root)
                       | (Q(
            folderpermission__user=user,
            folderpermission__permission__in=[
                FolderPermissionEnum.FULL_ACCESS,
                FolderPermissionEnum.EDITOR,
                FolderPermissionEnum.VIEWER,
            ],
        ) & ~Q(
            creator=user
        ))
                       ).distinct()
        return qs


class postPage(LoginRequiredMixin, ListView):
    login_url = "/poste/login/"
    model = Post
    template_name = "contents.html"

    def get_context_data(self, **kwargs):
        context = super(postPage, self).get_context_data(**kwargs)
        # adds the folder you are viewing as a context object that can be accessed in the html template
        parent = Folder.objects.get(pk=self.kwargs['pk'])
        context["root"] = parent
        context["folders"] = Folder.objects.filter(parent=parent)
        return context

    def get_queryset(self, **kwargs):
        folder = Folder.objects.get(pk=self.kwargs['pk'])
        # checks that use has access to folder
        qs = super().get_queryset(**kwargs)
        qs = qs.filter(folder=folder)
        return qs

    def dispatch(self, *args, **kwargs):
        user = self.request.user
        folder = Folder.objects.get(pk=self.kwargs['pk'])
        # checks that use has access to folder
        if user.can_view_folder(folder):
            return super().dispatch(*args, **kwargs)
        else:
            return redirect("folders")


@login_required(login_url="/poste/login/")
def deleteFolder(request, pk):
    folder = Folder.objects.get(pk=pk)
    user = request.user
    userFolders = Folder.objects.filter(creator=user)
    if folder in userFolders:
        folder.delete()
    return redirect("folders")


@login_required(login_url="/poste/login/")
def delete_post(request, pk, pid):
    folder = Folder.objects.get(pk=pk)
    post = Post.objects.get(pk=pid)
    user = request.user
    permission = FolderPermission.objects.get(folder=folder, user=user)
    if permission.permission is FolderPermissionEnum.EDITOR or FolderPermissionEnum.FULL_ACCESS:
        post.delete()
    return redirect("folders")


@login_required(login_url="/poste/login/")
def delete_share(request, pk, uid):
    folder = Folder.objects.get(pk=pk)
    user = User.objects.get(pk=uid)
    share = FolderPermission.objects.get(folder=folder, user=user)
    if request.user.can_share_folder(folder):
        share.delete()
        return redirect("shareEdit", pk)
    return redirect("folders")


@login_required(login_url="/poste/login/")
def folder_share(request, pk):
    form = FolderShare()
    message = ''
    folder = Folder.objects.get(pk=pk)
    user = request.user
    share_target_user = None

    if user.can_share_folder(folder):
        if request.method == 'POST':
            form = FolderShare(request.POST)
            if form.is_valid():
                share_target = form.data['email']
                perm = form.data['permission']
                try:
                    share_target_user = User.objects.get(email=share_target)
                except User.DoesNotExist:
                    message = "User does not exists"
                if share_target_user is not None:
                    user.share_folder_with_user(folder, share_target_user, perm)
                    return redirect("folders")
    else:
        return redirect("folders")
    return render(request, 'folder_share.html', context={'form': form, 'message': message})


class FolderShares(LoginRequiredMixin, ListView):
    login_url = "/poste/login/"
    model = FolderPermission
    template_name = "folder_shares.html"

    def get_queryset(self, **kwargs):
        folder = Folder.objects.get(pk=self.kwargs['pk'])
        user = self.request.user
        qs = super().get_queryset(**kwargs)
        qs = qs.filter(folder=folder).distinct()
        qs = qs.exclude(user=user)
        return qs

    def dispatch(self, *args, **kwargs):
        user = self.request.user
        folder = Folder.objects.get(pk=self.kwargs['pk'])
        # checks that use has access to folder
        if user.can_share_folder(folder):
            return super().dispatch(*args, **kwargs)
        else:
            return redirect("folders")


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


@login_required(login_url="/poste/login/")
def folder_create(request, fid):
    form = FolderCreate
    message = ''
    root = Folder.objects.get(pk=fid)
    if request.method == 'POST':
        form = FolderCreate(request.POST)
        if form.is_valid() and (root.creator == request.user):

            new = request.user.create_folder_child(form.data['title'], root)
            return redirect("folders")
        else:
            message = "folder creation failed"
    return render(request, 'new_folder.html', context={'form': form, 'message': message})


@login_required(login_url="/poste/login/")
def post_create(request):
    form = PostCreate(user=request.user)
    message = ''
    if request.method == 'POST':
        form = PostCreate(request.POST, user=request.user)
        if form.is_valid():
            post = request.user.create_post(form.data['title'], form.data['url'],
                                            Folder.objects.get(pk=form.data['folder']))
            # pulls out the tags of the post
            tags_in = form.data['tags']
            tags = [tag.strip() for tag in tags_in.split(",") if tag.strip()]
            # adds the tags to the post that was created
            if tags:
                tag_list = []
                for tag_name in tags:
                    tag, _ = Tag.objects.get_or_create(name=tag_name)
                    tag_list.append(tag)
                post.tags.set(tag_list)
            return redirect("folders")
        else:
            message = "Post creation failed"
    return render(request, 'new_folder.html', context={'form': form, 'message': message})


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
def edit_profile(request):
    if request.method == 'POST':
        form = ProfileEdit(request.POST, instance=request.user)

        if form.is_valid():
            form.save()
            return redirect("folders")

    else:
        form = ProfileEdit(instance=request.user)

    return render(request, 'ProfileEdit.html', {'form': form})


@login_required(login_url="/poste/login/")
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, "Your password was updated")
            return redirect("edit_profile")
        else:
            messages.error(request, "error: ")
    else:
        form = PasswordChangeForm(request.user)

    return render(request, "update_password.html", {'form': form})


@login_required(login_url="/poste/login/")
def setting(request):
    return render(request, 'setting.html')


def logout_page(request):
    logout(request)
    return render(request, 'logout.html')
