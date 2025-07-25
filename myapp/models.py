from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
import uuid
from decimal import Decimal
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models
import uuid
from django.conf import settings


class User(AbstractUser):
    balance = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    hide_balance = models.BooleanField(default=False)
    referral_code = models.UUIDField(default=uuid.uuid4, editable=True, unique=True)
    referred_by = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='referrals')
    total_earned = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    
    # Add these to resolve the clashes
    groups = models.ManyToManyField(
        Group,
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name="custom_user_set",  # Changed from default
        related_query_name="user",
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name="custom_user_set",  # Changed from default
        related_query_name="user",
    )
    
    def get_referral_link(self):
        return f"http://yourdomain.com/register?ref={self.referral_code}"
class PasswordResetToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

class DepositPlan(models.Model):
    name = models.CharField(max_length=100)
    daily_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    referral_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    min_amount = models.DecimalField(max_digits=20, decimal_places=8)
    max_amount = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class WalletAddress(models.Model):
    WALLET_TYPES = (
        ('BTC', 'Bitcoin'),
        ('USDT', 'Tether (USDT)'),
        ('TRX', 'Tron (TRX)'),
        ('ETH', 'Ethereum'),
    )
    wallet_type = models.CharField(max_length=10, choices=WALLET_TYPES)
    address = models.CharField(max_length=100)
    qr_code = models.ImageField(upload_to='qr_codes/', null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.get_wallet_type_display()} - {self.address[:10]}..."

class Deposit(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    plan = models.ForeignKey(DepositPlan,  on_delete=models.CASCADE, blank=True,null=True)
    amount = models.DecimalField(max_digits=20, decimal_places=8, validators=[MinValueValidator(Decimal('0.00000001'))])
    wallet_type = models.CharField(max_length=10, choices=WalletAddress.WALLET_TYPES)
    proof = models.ImageField(upload_to='deposit_proofs/')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    transaction_hash = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - {self.amount} {self.wallet_type}"

class Withdrawal(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=20, decimal_places=8, validators=[MinValueValidator(Decimal('0.00000001'))])
    wallet_type = models.CharField(max_length=10, choices=WalletAddress.WALLET_TYPES)
    wallet_address = models.CharField(max_length=100)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.amount} {self.wallet_type}"

class Earning(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=20, decimal_places=8)
    source = models.CharField(max_length=100)  # 'deposit', 'referral', etc.
    deposit = models.ForeignKey(Deposit, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.amount} ({self.source})"