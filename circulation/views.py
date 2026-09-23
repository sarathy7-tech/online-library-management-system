from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.http import require_POST
from books.models import Book, BookCopy
from .models import Loan, Reservation, Fine
from .services import CirculationService
from users.decorators import role_required
from django.http import JsonResponse

@login_required
@role_required('Reader')
@require_POST
def borrow_book(request, copy_id):
    copy = get_object_or_404(BookCopy, id=copy_id)

    try:
        loan = CirculationService.borrow_book(request.user, copy)

        # If request is AJAX
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': f"Successfully borrowed '{copy.book.title}'.",
                'due_date': str(loan.due_date)
            })

        messages.success(request, f"Successfully borrowed '{copy.book.title}'.")
        return redirect('books:book_detail', book_id=copy.book.id)

    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=400)

        messages.error(request, str(e))
        return redirect('books:book_detail', book_id=copy.book.id)


@login_required
@role_required('Reader')
@require_POST
def return_book(request, loan_id):
    loan = get_object_or_404(Loan, id=loan_id, user=request.user)
    try:
        loan, fine = CirculationService.return_book(loan)
        if fine > 0:
            messages.warning(request, f"Book returned. Fine of ₹{fine} applied.")
        else:
            messages.success(request, "Book returned successfully.")
    except Exception as e:
        messages.error(request, str(e))
    return redirect('circulation:my_books')


@login_required
@role_required('Reader')
@require_POST
def renew_book(request, loan_id):
    loan = get_object_or_404(Loan, id=loan_id, user=request.user)
    try:
        CirculationService.renew_book(loan)
        messages.success(request, f"Book renewed successfully. New due date: {loan.due_date}")
    except Exception as e:
        messages.error(request, str(e))
    return redirect('circulation:my_books')


@login_required
@role_required('Reader')
@require_POST
def reserve_book(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    try:
        CirculationService.reserve_book(request.user, book)
        messages.success(request, f"Successfully reserved '{book.title}'.")
    except Exception as e:
        messages.error(request, str(e))
    return redirect('books:book_detail', book_id=book.id)


@login_required
@role_required('Reader')
@require_POST
def cancel_reservation(request, reservation_id):
    reservation = get_object_or_404(
        Reservation, id=reservation_id, user=request.user, status='Pending'
    )
    reservation.status = 'Cancelled'
    reservation.save()
    messages.success(request, f"Reservation for '{reservation.book.title}' cancelled.")
    return redirect('dashboard')


@login_required
@role_required('Reader')
def my_books(request):
    loans = Loan.objects.filter(user=request.user).select_related('copy__book').order_by('-loan_date')
    return render(request, 'circulation/my_books.html', {'loans': loans})


@login_required
@role_required('Reader')
def pay_fine(request, fine_id):
    fine = get_object_or_404(Fine, id=fine_id, user=request.user)
    if request.method == 'POST':
        fine.status = 'Paid'
        fine.paid_amount = fine.amount
        fine.payment_date = timezone.now().date()
        fine.save()

        # Update user total fines
        user = request.user
        user.total_fines = max(user.total_fines - fine.amount, 0)
        user.save()

        messages.success(request, "Fine paid successfully!")
        return redirect('circulation:my_books')

    return render(request, 'circulation/pay_fine.html', {'fine': fine})