"""
Formulários da aplicação
"""
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Order, Product, Transaction


class UserRegistrationForm(UserCreationForm):
    """Formulário de registo de utilizador"""
    email = forms.EmailField(required=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'user_type', 'phone', 'password1', 'password2']


class OrderForm(forms.ModelForm):
    """Formulário de criação de pedido"""
    
    class Meta:
        model = Order
        fields = ['scheduled_date', 'scheduled_time', 'payment_method', 'notes']
        widgets = {
            'scheduled_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'scheduled_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'payment_method': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }


class TopUpForm(forms.ModelForm):
    """Formulário de carregamento de saldo"""
    
    class Meta:
        model = Transaction
        fields = ['amount']
        widgets = {
            'amount': forms.NumberInput(attrs={'min': '5', 'step': '0.01', 'class': 'form-control'}),
        }


class ProductForm(forms.ModelForm):
    """Formulário de produto"""
    
    class Meta:
        model = Product
        fields = ['name', 'description', 'category', 'price', 'stock', 'min_stock', 'is_available', 'image']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }
