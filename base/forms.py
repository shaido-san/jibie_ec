from django import forms
from django.contrib.auth.forms import UserCreationForm
# base.Userをインポート
from .models import User

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        # ここでbase.Userを使用
        model = User
        fields = ["username", "email", "password1", "password2"]