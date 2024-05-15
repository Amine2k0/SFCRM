from django import forms
from .models import Ticket,Client,Agent,CustomUser
from django.contrib.auth.forms import UserCreationForm

class EditTicketform(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['Subject', 'Status']
        
    

class AddTicketform(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['Subject']  
    

class RegisterForm(UserCreationForm):
    username = forms.CharField(
        label=("Username"),
        strip=False,
        widget=forms.TextInput,
    )
    password1 = forms.CharField(
        label=("Password"),
        strip=False,
        widget=forms.PasswordInput,
    )
    password2 = forms.CharField(
        label=("Password confirmation"),
        widget=forms.PasswordInput,
        strip=False,
    )
    class Meta:
        model = Client 
        fields = ['username','age','adress','password1','password2']        


class LoginForm(forms.Form):
    username=forms.CharField()
    password=forms.CharField(widget=forms.PasswordInput)
    

class RegisterAForm(UserCreationForm):
    class Meta:
        model = Agent 
        fields = ['username','age','adress','password1','password2']  

