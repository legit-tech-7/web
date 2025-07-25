from celery import shared_task
from .models import Deposit, Earning
from django.utils import timezone

@shared_task
def calculate_daily_earnings():
    today = timezone.now().date()
    deposits = Deposit.objects.filter(status='approved')
    for deposit in deposits:
        percent = deposit.plan.daily_percent
        amount = (percent / 100) * deposit.amount
        if not Earning.objects.filter(deposit=deposit, date=today, source='daily').exists():
            Earning.objects.create(
                user=deposit.user,
                deposit=deposit,
                amount=amount,
                date=today,
                source='daily',
            )
