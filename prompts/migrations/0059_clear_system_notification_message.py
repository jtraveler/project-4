"""
Data migration: Clear message field on system notifications.

System notifications now store sanitized HTML in the title field only.
The message field was previously populated with the same content, causing
duplicate display (title + quote section).
"""
from django.db import migrations


def clear_system_notification_messages(apps, schema_editor):
    Notification = apps.get_model('prompts', 'Notification')
    count = Notification.objects.filter(
        is_admin_notification=True,
        notification_type='system',
    ).exclude(message='').update(message='')
    if count:
        print(f"  Cleared message field on {count} system notifications")


class Migration(migrations.Migration):

    dependencies = [
        ('prompts', '0058_add_notification_click_count'),
    ]

    operations = [
        migrations.RunPython(
            clear_system_notification_messages,
            migrations.RunPython.noop,
        ),
    ]
