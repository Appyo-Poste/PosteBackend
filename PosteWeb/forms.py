from django import forms
from django.db.models import Q
from django.contrib.auth.forms import PasswordChangeForm
from PosteAPI.models import User, Folder, Post, FolderPermissionEnum

import pprint

pp = pprint.PrettyPrinter(indent=4)


class LoginForm(forms.Form):
    username = forms.CharField(max_length=63)
    password = forms.CharField(max_length=63, widget=forms.PasswordInput)


class UpdatePasswordForm(PasswordChangeForm):
    pass


class RegisterForm(forms.ModelForm):
    email = forms.EmailField(required=True)
    password = forms.CharField(widget=forms.PasswordInput, min_length=8, max_length=32, help_text="must be at least 8 "
                                                                                                  "characters long")
    password_2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput, min_length=8, max_length=32)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']

    def clean_email(self):
        """
        Verify email is available.
        """
        email = self.cleaned_data.get('email')
        qs = User.objects.filter(email=email)
        if qs.exists():
            raise forms.ValidationError("email is taken")
        return email

    def clean(self):
        """
        # Verify both passwords match.
        """
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_2 = cleaned_data.get("password_2")
        if password is not None and password != password_2:
            self.add_error("password_2", "Your passwords must match")
        return cleaned_data

class ProfileEdit(forms.ModelForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']

    def clean_email(self):
        """
        Verify email is available.
        """
        email = self.cleaned_data.get('email')
        qs = User.objects.filter(email=email)
        if qs.exists() and self.instance.email != email:
            raise forms.ValidationError("email is taken")
        return email

    def save(self, commit=True):
        # Save the provided password in hashed format
        user = super().save(commit=False)
        if commit:
            user.save()
        return user


class FolderCreate(forms.ModelForm):
        class Meta:
            model = Folder
            fields = ('title',)

class FolderShare(forms.Form):
    email = forms.EmailField(required=True)
    permission = forms.ChoiceField(choices=FolderPermissionEnum.choices,)

class PostCreate(forms.ModelForm):
    tags = forms.CharField()
    class Meta:
        model = Post
        fields = ('title', 'description', 'url', 'folder')

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        qs = Folder.objects.filter(Q(creator=user)
                       | Q(
            folderpermission__user=user,
            folderpermission__permission__in=[
                FolderPermissionEnum.FULL_ACCESS,
                FolderPermissionEnum.EDITOR,
            ],
        )
                       ).distinct()
        super(PostCreate, self).__init__(*args, **kwargs)
        self.fields['folder'].queryset = qs

