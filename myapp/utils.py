from datetime import date
from .models import Deposit, Earning
from decimal import Decimal

def process_daily_earnings():
    today = date.today()
    deposits = Deposit.objects.filter(status='APPROVED')

    for deposit in deposits:
        user = deposit.user
        plan = deposit.plan

        if not plan or not plan.daily_percentage:
            continue

        already_exists = Earning.objects.filter(
            user=user,
            source='daily',
            deposit=deposit,
            created_at__date=today
        ).exists()

        if already_exists:
            continue

        amount = deposit.amount * (plan.daily_percentage / Decimal('100'))

        # Create earning
        Earning.objects.create(
            user=user,
            amount=amount,
            source='daily',
            deposit=deposit
        )

        # Update user balance and total earned
        user.balance += amount
        user.total_earned += amount
        user.save()
