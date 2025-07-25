from django.contrib import admin

# Register your models here.
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, DepositPlan, WalletAddress, Deposit, Withdrawal, Earning

# Custom User Admin
class CustomUserAdmin(UserAdmin):
    # Fields to display in the list view
    list_display = ('username', 'email', 'balance', 'total_earned', 'is_staff')
    
    # Fields to filter by
    list_filter = ('is_staff', 'is_superuser', 'is_active')
    
    # Fieldsets for add/edit pages
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('email', 'balance', 'hide_balance', 'total_earned', 'referred_by')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    # Fields for the add user page
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'balance'),
        }),
    )
    
    # Make balance editable in list view
    list_editable = ('balance',)
    
    # Search fields
    search_fields = ('username', 'email', 'referral_code')
    
    # Ordering
    ordering = ('-date_joined',)

from django.contrib import admin
from django.utils import timezone
from .models import Deposit

class DepositAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'wallet_type', 'status', 'created_at', 'plan')
    list_filter = ('status', 'wallet_type', 'created_at')
    search_fields = ('user__username', 'transaction_hash')
    readonly_fields = ('created_at', 'approved_at')
    list_editable = ('status',)

    def save_model(self, request, obj, form, change):
        print(f"[DEBUG] Saving Deposit: ID={obj.id}, Status={obj.status}, Change={change}")

        if not change:
            # New deposit
            if obj.status == 'APPROVED':
                print("[DEBUG] New deposit created with APPROVED status — updating balance.")
                obj.approved_at = timezone.now()
                obj.user.balance += obj.amount
                obj.user.save()

        else:
            # Existing deposit being edited
            old_obj = Deposit.objects.get(pk=obj.pk)
            print(f"[DEBUG] Previous Status: {old_obj.status}")

            if old_obj.status != 'APPROVED' and obj.status == 'APPROVED':
                print("[DEBUG] Status changed to APPROVED — updating balance.")
                obj.approved_at = timezone.now()
                obj.user.balance += obj.amount
                obj.user.save()

        super().save_model(request, obj, form, change)

            

from django.contrib import admin
from django.utils import timezone
from .models import Withdrawal

class WithdrawalAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'wallet_type', 'status', 'created_at')
    list_filter = ('status', 'wallet_type', 'created_at')
    search_fields = ('user__username', 'wallet_address')
    readonly_fields = ('created_at', 'approved_at')
    list_editable = ('status',)

    def save_model(self, request, obj, form, change):
        print(f"[DEBUG] Saving Withdrawal: ID={obj.id}, Status={obj.status}, Change={change}")

        if not change:
            # New withdrawal
            if obj.status == 'APPROVED':
                print("[DEBUG] New withdrawal created with APPROVED status — deducting balance.")
                obj.approved_at = timezone.now()
                obj.user.balance -= obj.amount
                obj.user.save()

        else:
            # Editing existing withdrawal
            old_obj = Withdrawal.objects.get(pk=obj.pk)
            print(f"[DEBUG] Previous Status: {old_obj.status}")

            if old_obj.status != 'APPROVED' and obj.status == 'APPROVED':
                print("[DEBUG] Status changed to APPROVED — deducting balance.")
                obj.approved_at = timezone.now()
                obj.user.balance -= obj.amount
                obj.user.save()

        super().save_model(request, obj, form, change)

# Earning Admin
class EarningAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'source', 'created_at')
    list_filter = ('source', 'created_at')
    search_fields = ('user__username',)
    readonly_fields = ('created_at',)


class DepositPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'daily_percentage', 'min_amount', 'is_active')
    # Exclude user field if it exists but shouldn't be set
    

# Register models
admin.site.register(User, CustomUserAdmin)
admin.site.register(DepositPlan,DepositPlanAdmin)
admin.site.register(WalletAddress)
admin.site.register(Deposit, DepositAdmin)
admin.site.register(Withdrawal, WithdrawalAdmin)
admin.site.register(Earning, EarningAdmin)