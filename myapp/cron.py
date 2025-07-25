from django_cron import CronJobBase, Schedule # type: ignore
from .models import Deposit, Earning
from django.utils import timezone

class DailyEarningCronJob(CronJobBase):
    RUN_AT_TIMES = ['00:00']  # Run at midnight

    schedule = Schedule(run_at_times=RUN_AT_TIMES)
    code = 'myapp.daily_earning_cron'

    def do(self):
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
                    source='daily'
                )
