# ✅ FULLY UPDATED VIEWS.PY WITH EMAIL NOTIFICATIONS FOR ALL USER ACTIONS

from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.utils.crypto import get_random_string
from django.urls import reverse
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db import transaction
from django.db.models import Sum
from decimal import Decimal
import uuid
from datetime import timedelta

from .models import User, PasswordResetToken, Deposit, Withdrawal, WalletAddress, DepositPlan, Earning
from .forms import RegistrationForm, CustomPasswordResetForm, CustomSetPasswordForm, DepositForm, WithdrawalForm


import threading
from django.core.mail import send_mail
from django.conf import settings

def send_notification(user, subject, message):
    if not user.email:
        return

    def send():
        try:
            send_mail(
                subject,
                message,
                settings.EMAIL_HOST_USER,
                [user.email],
                fail_silently=False,
            )
        except Exception as e:
            print("❌ Email failed:", e)

    # Run email in background
    threading.Thread(target=send).start()



def register_view(request):
    referral_code = request.GET.get('ref', '')  # Read from URL

    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)

            # Handle referral logic
            if referral_code:
                try:
                    referrer = User.objects.get(referral_code=referral_code)
                    user.referred_by = referrer
                except User.DoesNotExist:
                    pass  # Ignore if code invalid

            user.save()
            login(request, user)

            # Send welcome email
            send_notification(user, "Welcome", f"Hi {user.username}, your account has been created!")

            # Send referral notification
            if user.referred_by:
                send_notification(user.referred_by, "New Referral",
                                  f"{user.username} signed up using your referral link!")

            messages.success(request, "Registration successful!")
            return redirect('dashboard')
    else:
        form = RegistrationForm()

    return render(request, 'myapp/register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, 'Login successful!')
            send_notification(user, "Login Alert", f"You just logged in to your account.")
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password')
    
    return render(request, 'myapp/login.html')

def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out')
    return redirect('login')

def forgot_password(request):
    if request.method == 'POST':
        form = CustomPasswordResetForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = User.objects.get(email=email)
                token = get_random_string(length=6, allowed_chars='0123456789')
                PasswordResetToken.objects.create(user=user, token=token)

                reset_link = request.build_absolute_uri(
                    reverse('reset_password_confirm', kwargs={'token': token})
                )

                send_notification(user, "Password Reset Code",
                    f"Your 6-digit reset code is: {token}\nOr reset here: {reset_link}")

                messages.success(request, 'A 6-digit code has been sent to your email')
                return redirect('reset_password_confirm', token=token)
            except User.DoesNotExist:
                messages.error(request, 'No user with that email address')
    else:
        form = CustomPasswordResetForm()
    
    return render(request, 'myapp/forgot_password.html', {'form': form})

def reset_password_confirm(request, token):
    try:
        reset_token = PasswordResetToken.objects.get(
            token=token, is_used=False,
            created_at__gte=timezone.now() - timedelta(hours=1)
        )

        if request.method == 'POST':
            form = CustomSetPasswordForm(reset_token.user, request.POST)
            if form.is_valid():
                form.save()
                reset_token.is_used = True
                reset_token.save()

                send_notification(reset_token.user, "Password Reset",
                    "Your password was successfully reset.")

                messages.success(request, 'Password reset successfully!')
                return redirect('login')
        else:
            form = CustomSetPasswordForm(reset_token.user)
        
        return render(request, 'myapp/reset_password.html', {'form': form, 'token': token})
    except PasswordResetToken.DoesNotExist:
        messages.error(request, 'Invalid or expired token')
        return redirect('forgot_password')


# ✅ Dashboard Views
@login_required
def dashboard(request):
    user = request.user

    deposits = Deposit.objects.filter(user=user).order_by('-created_at')[:5]
    withdrawals = Withdrawal.objects.filter(user=user).order_by('-created_at')[:5]
    earnings = Earning.objects.filter(user=user).order_by('-created_at')[:5]

    total_earned = Earning.objects.filter(user=user).aggregate(total=Sum('amount'))['total'] or Decimal('0.0')
    referral_earned = Earning.objects.filter(user=user, source='referral').aggregate(total=Sum('amount'))['total'] or Decimal('0.0')
    daily_earned = Earning.objects.filter(user=user, source='daily_earning').aggregate(total=Sum('amount'))['total'] or Decimal('0.0')

    context = {
        'deposits': deposits,
        'withdrawals': withdrawals,
        'earnings': earnings,
        'total_earned': total_earned,
        'referral_earned': referral_earned,
        'daily_earned': daily_earned,
        'balance': user.balance,
        'wallet_addresses': WalletAddress.objects.filter(is_active=True),
        'deposit_plans': DepositPlan.objects.filter(is_active=True),
    }
    return render(request, 'myapp/dashboard.html', context)


@login_required
def deposit_history(request):
    deposits = Deposit.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'myapp/deposit_history.html', {'deposits': deposits})

@login_required
def withdrawal_history(request):
    withdrawals = Withdrawal.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'myapp/withdrawal_history.html', {'withdrawals': withdrawals})

@login_required
def earnings_history(request):
    earnings = Earning.objects.filter(user=request.user).order_by('-created_at')
    deposit_earnings = Earning.objects.filter(user=request.user, source='deposit').aggregate(total=Sum('amount'))['total'] or 0
    referral_earnings = Earning.objects.filter(user=request.user, source='referral').aggregate(total=Sum('amount'))['total'] or 0
    return render(request, 'myapp/earnings_history.html', {
        'earnings': earnings,
        'total_earned': deposit_earnings + referral_earnings,
        'deposit_earnings': deposit_earnings,
        'referral_earnings': referral_earnings,
    })


# ✅ Transaction Views
@login_required
def create_deposit(request):
    if request.method == 'POST':
        form = DepositForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            deposit = form.save(commit=False)
            deposit.user = request.user
            deposit.status = 'PENDING'
            deposit.save()

            admin_emails = User.objects.filter(is_staff=True).values_list('email', flat=True)
            approve_url = request.build_absolute_uri(
                reverse('approve_deposit', kwargs={'deposit_id': deposit.id})
            )

            # Notify admin
            send_mail(
                'New Deposit Request',
                f'{request.user.username} made a deposit of {deposit.amount}. Approve: {approve_url}',
                settings.EMAIL_HOST_USER,
                admin_emails,
                fail_silently=False,
            )

            # Notify user
            send_notification(request.user, "Deposit Received", "Your deposit request is pending admin approval.")

            messages.success(request, 'Deposit submitted successfully!')
            return redirect('dashboard')
    else:
        form = DepositForm(user=request.user)

    return render(request, 'myapp/create_deposit.html', {
        'form': form,
        'wallet_addresses': WalletAddress.objects.filter(is_active=True),
        'plans': DepositPlan.objects.filter(is_active=True),
    })


@login_required
def create_withdrawal(request):
    if request.method == 'POST':
        form = WithdrawalForm(request.POST, user=request.user)
        if form.is_valid():
            withdrawal = form.save(commit=False)
            withdrawal.user = request.user
            withdrawal.save()

            request.user.balance -= withdrawal.amount
            request.user.save()

            admin_emails = User.objects.filter(is_staff=True).values_list('email', flat=True)
            approve_url = request.build_absolute_uri(
                reverse('approve_withdrawal', kwargs={'withdrawal_id': withdrawal.id})
            )

            send_mail(
                'New Withdrawal Request',
                f'{request.user.username} requested {withdrawal.amount} withdrawal.\nApprove: {approve_url}',
                settings.EMAIL_HOST_USER,
                admin_emails,
                fail_silently=False,
            )

            send_notification(request.user, "Withdrawal Submitted", "Your withdrawal is pending approval.")
            messages.success(request, 'Withdrawal request submitted!')
            return redirect('dashboard')
    else:
        form = WithdrawalForm(user=request.user)

    return render(request, 'myapp/create_withdrawal.html', {'form': form})


# ✅ Admin Views
@login_required
def admin_approve_deposit(request, deposit_id):
    if not request.user.is_staff:
        return HttpResponseForbidden()
    
    deposit = Deposit.objects.get(id=deposit_id)
    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'approve':
            deposit.status = 'APPROVED'
            deposit.approved_at = timezone.now()
            deposit.save()

            # ✅ Add deposit amount to user balance
            deposit.user.balance += deposit.amount
            deposit.user.save()

            # ✅ Record earning for the depositor
            Earning.objects.create(
                user=deposit.user,
                amount=deposit.amount,
                source='deposit',
                deposit=deposit
            )

            # ✅ Email depositor
            send_notification(
                deposit.user,
                "Deposit Approved",
                f"Your deposit of ${deposit.amount:.2f} has been approved."
            )

            # ✅ Handle referral bonus
            if deposit.user.referred_by and deposit.plan and deposit.plan.referral_percentage > 0:
                referral_bonus = deposit.amount * (deposit.plan.referral_percentage / 100)
                referrer = deposit.user.referred_by

                referrer.balance += referral_bonus
                referrer.total_earned += referral_bonus
                referrer.save()

                Earning.objects.create(
                    user=referrer,
                    amount=referral_bonus,
                    source='referral',
                    deposit=deposit
                )

                # ✅ Email referrer
                send_notification(
                    referrer,
                    "Referral Bonus Earned",
                    f"You earned ${referral_bonus:.2f} because {deposit.user.username} made a deposit!"
                )

            messages.success(request, 'Deposit approved!')
            return redirect('admin_dashboard')

        elif action == 'reject':
            deposit.status = 'REJECTED'
            deposit.save()

            send_notification(
                deposit.user,
                "Deposit Rejected",
                "Your deposit was rejected."
            )

            messages.success(request, 'Deposit rejected.')
            return redirect('admin_dashboard')

    return render(request, 'myapp/admin_approve_deposit.html', {'deposit': deposit})



@login_required
def admin_approve_withdrawal(request, withdrawal_id):
    if not request.user.is_staff:
        return HttpResponseForbidden()

    withdrawal = Withdrawal.objects.get(id=withdrawal_id)
    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'approve':
            withdrawal.status = 'APPROVED'
            withdrawal.approved_at = timezone.now()
            withdrawal.save()
            send_notification(withdrawal.user, "Withdrawal Approved", f"Your withdrawal of {withdrawal.amount} has been approved.")
            messages.success(request, 'Withdrawal approved!')
            return redirect('admin_dashboard')

        elif action == 'reject':
            withdrawal.user.balance += withdrawal.amount
            withdrawal.user.save()
            withdrawal.status = 'REJECTED'
            withdrawal.save()
            send_notification(withdrawal.user, "Withdrawal Rejected", f"Your withdrawal was rejected. Funds returned.")
            messages.success(request, 'Withdrawal rejected.')
            return redirect('admin_dashboard')

    return render(request, 'myapp/admin_approve_withdrawal.html', {'withdrawal': withdrawal})


@login_required
def admin_dashboard(request):
    if not request.user.is_staff:
        return HttpResponseForbidden()

    return render(request, 'myapp/admin_dashboard.html', {
        'pending_deposits': Deposit.objects.filter(status='PENDING'),
        'pending_withdrawals': Withdrawal.objects.filter(status='PENDING'),
        'total_users': User.objects.count(),
    })


# ✅ AJAX View
@login_required
@require_POST
def toggle_balance_visibility(request):
    request.user.hide_balance = not request.user.hide_balance
    request.user.save()
    return JsonResponse({'hidden': request.user.hide_balance})


# ✅ Index and About Pages
def index(request):
    return render(request, 'myapp/index.html')

def about(request):
    return render(request, 'myapp/about.html')
