from datetime import timedelta, date
from django.db import transaction
from django.core.exceptions import ValidationError
from decimal import Decimal
from .models import Loan, Fine, Reservation
from books.models import BookCopy
from users.notifications import create_notification


class CirculationService:

    FINE_PER_DAY = Decimal('5.00')
    MAX_BORROW_DAYS = 14
    MAX_RENEW_DAYS = 7
    MAX_RENEWS = 2

    @staticmethod
    @transaction.atomic
    def borrow_book(user, copy):
        if copy.status != 'Available':
            raise ValidationError("This book copy is not available.")

        if user.total_fines > 0:
            raise ValidationError("Please clear your outstanding fines before borrowing.")

        active_loans = Loan.objects.filter(user=user, status__in=['Active', 'Overdue']).count()
        if active_loans >= user.borrowing_limit:
            raise ValidationError(f"You have reached your borrowing limit ({user.borrowing_limit} books).")

        due_date = date.today() + timedelta(days=CirculationService.MAX_BORROW_DAYS)

        loan = Loan.objects.create(
            user=user,
            copy=copy,
            due_date=due_date,
            status='Active'
        )

        copy.status = 'Issued'
        copy.save()

        book = copy.book
        book.available_copies = book.copies.filter(status='Available').count()
        book.save()

        # Notification (BEFORE return)
        create_notification(
            user=user,
            title='Book Borrowed Successfully',
            message=f'You borrowed "{copy.book.title}". Due date: {due_date}.',
            notification_type='general',
            link='/circulation/my-books/',
            send_email=False
        )

        return loan

    @staticmethod
    @transaction.atomic
    def return_book(loan):
        if loan.status == 'Returned':
            raise ValidationError("This book is already returned.")

        today = date.today()
        loan.return_date = today
        loan.status = 'Returned'

        fine_amount = Decimal('0.00')
        if loan.due_date < today:
            days_overdue = (today - loan.due_date).days
            fine_amount = Decimal(days_overdue) * CirculationService.FINE_PER_DAY
            loan.fine_amount = fine_amount

            Fine.objects.create(
                loan=loan,
                user=loan.user,
                amount=fine_amount,
                status='Unpaid'
            )
            loan.user.total_fines += fine_amount
            loan.user.save()

        loan.save()

        copy = loan.copy
        copy.status = 'Available'
        copy.save()

        book = copy.book
        book.available_copies = book.copies.filter(status='Available').count()
        book.save()

        # Notifications (BEFORE return)
        if fine_amount > 0:
            create_notification(
                user=loan.user,
                title='Fine Applied',
                message=f'A fine of ₹{fine_amount} was applied for overdue book "{loan.copy.book.title}".',
                notification_type='fine',
                link='/fines/',
                send_email=True
            )
        else:
            create_notification(
                user=loan.user,
                title='Book Returned',
                message=f'You successfully returned "{loan.copy.book.title}".',
                notification_type='general',
                link='/circulation/my-books/',
                send_email=False
            )

        # Notify reservation users
        pending_reservations = Reservation.objects.filter(
            book=copy.book,
            status='Pending'
        ).select_related('user')

        for reservation in pending_reservations:
            create_notification(
                user=reservation.user,
                title='Reserved Book Available',
                message=f'Good news! "{copy.book.title}" is now available. Please borrow it soon.',
                notification_type='reservation',
                link=f'/books/{copy.book.id}/',
                send_email=True
            )

        return loan, fine_amount

    @staticmethod
    @transaction.atomic
    def renew_book(loan):
        if loan.status not in ['Active', 'Overdue']:
            raise ValidationError("Only active or overdue loans can be renewed.")

        if loan.fine_amount and loan.fine_amount > 0:
            raise ValidationError("Please clear the fine before renewing.")

        loan.due_date = loan.due_date + timedelta(days=CirculationService.MAX_RENEW_DAYS)
        loan.status = 'Active'
        loan.save()

        create_notification(
            user=loan.user,
            title='Book Renewed',
            message=f'Your book "{loan.copy.book.title}" was renewed. New due date: {loan.due_date}.',
            notification_type='general',
            link='/circulation/my-books/',
            send_email=False
        )

        return loan

    @staticmethod
    @transaction.atomic
    def reserve_book(user, book):
        existing = Reservation.objects.filter(user=user, book=book, status='Pending').exists()
        if existing:
            raise ValidationError("You already have a pending reservation for this book.")

        available = book.copies.filter(status='Available').exists()
        if available:
            raise ValidationError("This book is currently available. You can borrow it directly.")

        reservation = Reservation.objects.create(
            user=user,
            book=book,
            expiry_date=date.today() + timedelta(days=7),
            status='Pending'
        )

        create_notification(
            user=user,
            title='Book Reserved',
            message=f'You reserved "{book.title}". We will notify you when it becomes available.',
            notification_type='reservation',
            link='/dashboard/',
            send_email=False
        )

        return reservation