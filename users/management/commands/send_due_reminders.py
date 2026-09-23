from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from circulation.models import Loan
from users.notifications import create_notification

class Command(BaseCommand):
    help = 'Send notifications for books due tomorrow and overdue books'

    def handle(self, *args, **options):
        today = timezone.now().date()
        tomorrow = today + timedelta(days=1)

        # Books due tomorrow
        due_tomorrow = Loan.objects.filter(
            status='Active',
            due_date=tomorrow
        ).select_related('user', 'copy__book')

        count_due = 0
        for loan in due_tomorrow:
            create_notification(
                user=loan.user,
                title='Book Due Tomorrow',
                message=f'Your book "{loan.copy.book.title}" is due tomorrow ({loan.due_date}).',
                notification_type='due_soon',
                link='/circulation/my-books/',
                send_email=True
            )
            count_due += 1

        # Overdue books
        overdue = Loan.objects.filter(
            status='Active',
            due_date__lt=today
        ).select_related('user', 'copy__book')

        count_overdue = 0
        for loan in overdue:
            create_notification(
                user=loan.user,
                title='Book Overdue',
                message=f'Your book "{loan.copy.book.title}" was due on {loan.due_date}. Please return it soon.',
                notification_type='overdue',
                link='/circulation/my-books/',
                send_email=True
            )
            count_overdue += 1

        self.stdout.write(self.style.SUCCESS(
            f'Done! Due tomorrow: {count_due}, Overdue: {count_overdue}'
        ))