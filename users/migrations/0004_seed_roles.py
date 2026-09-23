from django.db import migrations


ROLE_NAMES = ['Admin', 'Librarian', 'Reader']


def seed_roles(apps, schema_editor):
    """
    Create the three roles the whole app assumes exist (registration,
    reader/staff dashboards, createsuperuser all look one of these up by
    name). Previously this had to be done by hand in `manage.py shell`.
    Uses get_or_create so it's safe to run against a database that
    already has some or all of these roles.
    """
    Role = apps.get_model('users', 'Role')
    for name in ROLE_NAMES:
        Role.objects.get_or_create(role_name=name)


def unseed_roles(apps, schema_editor):
    # Intentionally a no-op on reverse: if users already reference these
    # roles (role is on_delete=PROTECT), deleting them here would either
    # crash the migration or silently break existing accounts.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0003_notification"),
    ]

    operations = [
        migrations.RunPython(seed_roles, reverse_code=unseed_roles),
    ]
