from django import forms
from django.contrib.auth.forms import UserCreationForm
# base.Userをインポート
from .models import User, Address

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        # ここでbase.Userを使用
        model = User
        fields = ["username", "email", "password1", "password2"]
    
class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ["post_code", "address", "name", "telephone_number"]