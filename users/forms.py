from django import forms
from api.models import User

class UserForm(forms.Form):
    token = forms.CharField(label='Token', max_length=128)