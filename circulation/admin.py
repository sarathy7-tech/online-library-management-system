from django.contrib import admin
from .models import Loan, Reservation, Fine

@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = ('user', 'copy', 'loan_date', 'due_date', 'status', 'fine_amount')
    list_filter = ('status', 'loan_date', 'due_date')
    search_fields = ('user__username', 'copy__book__title')
    readonly_fields = ('fine_amount',)

@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ('user', 'book', 'reservation_date', 'expiry_date', 'status')
    list_filter = ('status',)
    search_fields = ('user__username', 'book__title')

@admin.register(Fine)
class FineAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'status', 'fine_date', 'paid_amount')
    list_filter = ('status',)
    search_fields = ('user__username',)