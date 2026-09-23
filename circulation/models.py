from django.db import models

# Create your models here.
from django.db import models
from django.utils import timezone
from datetime import timedelta

class Loan(models.Model):
    user = models.ForeignKey('users.CustomUser', on_delete=models.CASCADE, related_name='loans')
    copy = models.ForeignKey('books.BookCopy', on_delete=models.CASCADE)
    loan_date = models.DateField(auto_now_add=True)
    due_date = models.DateField()
    return_date = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('Active', 'Active'),
            ('Returned', 'Returned'),
            ('Overdue', 'Overdue'),
            ('Lost', 'Lost')
        ],
        default='Active'
    )
    fine_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.user} - {self.copy}"

    def save(self, *args, **kwargs):
        if not self.due_date:
            # NOTE: self.loan_date is only populated by auto_now_add once
            # super().save() actually runs, so it's still None here on a
            # brand-new loan. Use "today" directly instead.
            self.due_date = timezone.now().date() + timedelta(days=14)
        super().save(*args, **kwargs)

class Reservation(models.Model):
    user = models.ForeignKey('users.CustomUser', on_delete=models.CASCADE, related_name='reservations')
    book = models.ForeignKey('books.Book', on_delete=models.CASCADE)
    reservation_date = models.DateField(auto_now_add=True)
    expiry_date = models.DateField()
    status = models.CharField(
        max_length=20,
        choices=[
            ('Pending', 'Pending'),
            ('Fulfilled', 'Fulfilled'),
            ('Cancelled', 'Cancelled'),
            ('Expired', 'Expired')
        ],
        default='Pending'
    )

    def __str__(self):
        return f"{self.user} reserved {self.book}"

class Fine(models.Model):
    loan = models.ForeignKey(Loan, on_delete=models.SET_NULL, null=True, blank=True)
    user = models.ForeignKey('users.CustomUser', on_delete=models.CASCADE, related_name='fines')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    fine_date = models.DateField(auto_now_add=True)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(
        max_length=20,
        choices=[
            ('Unpaid', 'Unpaid'),
            ('Partially Paid', 'Partially Paid'),
            ('Paid', 'Paid')
        ],
        default='Unpaid'
    )
    payment_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"Fine for {self.user} - {self.amount}"