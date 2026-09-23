from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.reader_dashboard, name='dashboard'),
    path('readers/', views.reader_list, name='reader_list'),
    path('readers/create/', views.create_reader, name='create_reader'),
    path('readers/<int:user_id>/', views.reader_detail, name='reader_detail'),
    path('readers/<int:user_id>/edit/', views.edit_reader, name='edit_reader'),
    path('readers/<int:user_id>/delete/', views.delete_reader, name='delete_reader'),
    path('staff-dashboard/', views.staff_dashboard, name='staff_dashboard'),


    # ========== Password Reset ==========
    path('password-reset/', 
         auth_views.PasswordResetView.as_view(
             template_name='users/password_reset.html'
         ), 
         name='password_reset'),

    path('password-reset/done/', 
         auth_views.PasswordResetDoneView.as_view(
             template_name='users/password_reset_done.html'
         ), 
         name='password_reset_done'),

    path('password-reset-confirm/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(
             template_name='users/password_reset_confirm.html'
         ), 
         name='password_reset_confirm'),

    path('password-reset-complete/', 
         auth_views.PasswordResetCompleteView.as_view(
             template_name='users/password_reset_complete.html'
         ), 
         name='password_reset_complete'),

    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/library-card/', views.download_library_card, name='library_card'),
    path('fines/', views.fine_history, name='fine_history'),

    path('reports/', views.reports, name='reports'),

    path('reports/export/most-borrowed/', views.export_most_borrowed_excel, name='export_most_borrowed'),
path('reports/export/fines/', views.export_fines_excel, name='export_fines'),
path('reports/export/active-readers/', views.export_active_readers_excel, name='export_active_readers'),


path('notifications/', views.get_notifications, name='get_notifications'),
path('notifications/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
path('notifications/read-all/', views.mark_all_notifications_read, name='mark_all_read'),
]