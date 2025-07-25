from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordResetForm, SetPasswordForm
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from .models import User, Deposit, Withdrawal, DepositPlan

class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    referral_code = forms.CharField(required=False, widget=forms.HiddenInput())  # Changed to hidden input

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove referral_code from visible fields if you want to handle it separately
        self.fields.pop('referral_code', None)

    def clean(self):
        cleaned_data = super().clean()
        referral_code = self.data.get('referral_code')  # Get from request data
        
        if referral_code:
            try:
                referrer = User.objects.get(referral_code=referral_code)
                cleaned_data['referred_by'] = referrer
            except User.DoesNotExist:
                raise ValidationError("Invalid referral code")
        
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        if 'referred_by' in self.cleaned_data:
            user.referred_by = self.cleaned_data['referred_by']
        if commit:
            user.save()
        return user

class CustomPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(
        label="Email",
        max_length=254,
        widget=forms.EmailInput(attrs={'autocomplete': 'email', 'class': 'form-control'})
    )

class CustomSetPasswordForm(SetPasswordForm):
    new_password1 = forms.CharField(
        label="New password",
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password', 'class': 'form-control'}),
        strip=False,
    )
    new_password2 = forms.CharField(
        label="New password confirmation",
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password', 'class': 'form-control'}),
    )

class DepositForm(forms.ModelForm):
    class Meta:
        model = Deposit
        fields = ['plan', 'amount', 'wallet_type', 'proof', 'transaction_hash']
        widgets = {
            'plan': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'wallet_type': forms.Select(attrs={'class': 'form-select'}),
            'transaction_hash': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.fields['proof'].widget.attrs.update({'class': 'form-control'})

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        plan = self.cleaned_data.get('plan')
        
        if plan and amount:
            if amount < plan.min_amount:
                raise ValidationError(f"Minimum deposit amount for this plan is {plan.min_amount}")
            if plan.max_amount and amount > plan.max_amount:
                raise ValidationError(f"Maximum deposit amount for this plan is {plan.max_amount}")
        
        return amount

class WithdrawalForm(forms.ModelForm):
    class Meta:
        model = Withdrawal
        fields = ['amount', 'wallet_type', 'wallet_address']
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'wallet_type': forms.Select(attrs={'class': 'form-select'}),
            'wallet_address': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if self.user and amount > self.user.balance:
            raise ValidationError("Insufficient balance for this withdrawal")
        return amount