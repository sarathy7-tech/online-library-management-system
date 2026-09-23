from django.urls import path
from . import views

app_name = 'circulation'

urlpatterns = [
    path('borrow/<int:copy_id>/', views.borrow_book, name='borrow_book'),
    path('return/<int:loan_id>/', views.return_book, name='return_book'),
    path('renew/<int:loan_id>/', views.renew_book, name='renew_book'),
    path('reserve/<int:book_id>/', views.reserve_book, name='reserve_book'),
    path('reservation/<int:reservation_id>/cancel/', views.cancel_reservation, name='cancel_reservation'),
    path('my-books/', views.my_books, name='my_books'),
    path('pay-fine/<int:fine_id>/', views.pay_fine, name='pay_fine'),
]