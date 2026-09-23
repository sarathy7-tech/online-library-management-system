from django.core.management.base import BaseCommand
from django.utils import timezone
from circulation.models import Reservation
from users.notifications import create_notification


class Command(BaseCommand):
    help = (
        "Expire pending reservations whose expiry_date has passed. "
        "The 'Expired' status already existed on the Reservation model "
        "but nothing ever set it - reservations just sat as 'Pending' "
        "forever. Run this daily (e.g. via cron or Task Scheduler), the "
        "same way you'd run send_due_reminders."
    )

    def handle(self, *args, **options):
        today = timezone.now().date()

        stale = Reservation.objects.filter(
            status='Pending',
            expiry_date__lt=today
        ).select_related('user', 'book')

        count = 0
        for reservation in stale:
            reservation.status = 'Expired'
            reservation.save(update_fields=['status'])

            create_notification(
                user=reservation.user,
                title='Reservation Expired',
                message=f'Your reservation for "{reservation.book.title}" expired on {reservation.expiry_date}.',
                notification_type='reservation',
                link='/dashboard/',
                send_email=True
            )
            count += 1

        self.stdout.write(self.style.SUCCESS(f'Done! Expired {count} reservation(s).'))
