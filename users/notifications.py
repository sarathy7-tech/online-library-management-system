from django.core.mail import send_mail
from django.conf import settings
from .models import Notification

def create_notification(user, title, message, notification_type='general', link=None, send_email=False):
    """Create in-app notification and optionally send email"""
    notification = Notification.objects.create(
        user=user,
        title=title,
        message=message,
        notification_type=notification_type,
        link=link
    )

    if send_email and user.email:
        try:
            full_message = f"""
Hello {user.get_full_name() or user.username},

{message}

---
Online Library Management System
Please do not reply to this email.
"""
            send_mail(
                subject=f'[Library] {title}',
                message=full_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
        except Exception as e:
            print(f"Failed to send email to {user.email}: {e}")

    return notification