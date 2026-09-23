from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models

class Role(models.Model):
    role_name = models.CharField(max_length=50, unique=True)
    
    def __str__(self):
        return self.role_name


class CustomUserManager(UserManager):
    """
    CustomUser.role is a required (non-nullable) foreign key, but Django's
    built-in `createsuperuser` command only fills in USERNAME_FIELD +
    REQUIRED_FIELDS (username, email, password) — it knows nothing about
    `role`. Left alone, `python manage.py createsuperuser` crashes with an
    IntegrityError because role_id is NULL.

    This manager auto-assigns a sensible default role (Admin for
    superusers, Reader for everyone else) whenever a caller doesn't
    explicitly provide one, so both `createsuperuser` and any ad-hoc
    `CustomUser.objects.create_user(...)` call keep working. Code that
    already sets `role` explicitly (register_view, create_reader, the
    Django admin "add user" form) is unaffected.
    """

    def _default_role(self, role_name):
        return Role.objects.get_or_create(role_name=role_name)[0]

    def create_user(self, username=None, email=None, password=None, **extra_fields):
        extra_fields.setdefault('role', self._default_role('Reader'))
        return super().create_user(username, email, password, **extra_fields)

    def create_superuser(self, username=None, email=None, password=None, **extra_fields):
        extra_fields.setdefault('role', self._default_role('Admin'))
        return super().create_superuser(username, email, password, **extra_fields)


class CustomUser(AbstractUser):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50, blank=True)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    role = models.ForeignKey(Role, on_delete=models.PROTECT)
    address = models.TextField(blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    membership_expiry = models.DateField(null=True, blank=True)
    borrowing_limit = models.IntegerField(default=5)
    total_fines = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    username = models.CharField(max_length=150, unique=True)

    objects = CustomUserManager()

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.role.role_name})"

    def is_admin(self):
        return self.role.role_name == 'Admin'

    def is_librarian(self):
        return self.role.role_name == 'Librarian'

    def is_reader(self):
        return self.role.role_name == 'Reader'


# AuditLog should be OUTSIDE the CustomUser class
class AuditLog(models.Model):
    user = models.ForeignKey('users.CustomUser', on_delete=models.SET_NULL, null=True)
    action_type = models.CharField(max_length=50)
    table_name = models.CharField(max_length=50, blank=True)
    record_id = models.IntegerField(null=True)
    old_values = models.JSONField(null=True, blank=True)
    new_values = models.JSONField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.action_type} by {self.user} at {self.created_at}"

class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('due_soon', 'Book Due Soon'),
        ('overdue', 'Book Overdue'),
        ('fine', 'Fine Reminder'),
        ('reservation', 'Reservation Available'),
        ('new_book', 'New Arrival'),
        ('general', 'General'),
    )

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='general')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    link = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.user.username}"