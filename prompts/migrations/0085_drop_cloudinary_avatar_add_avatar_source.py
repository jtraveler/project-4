"""Session 163-B: drop UserProfile.avatar CloudinaryField, rename
b2_avatar_url -> avatar_url, add avatar_source.

Zero avatars existed in production at time of migration (April 19 2026
diagnostic via migrate_cloudinary_to_b2 --dry-run). No data
preservation required.

v2 note: CC prepares this file only. The developer executes
`python manage.py migrate prompts` locally. See Session 163 run
instructions v2 for the migration handoff protocol.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('prompts', '0084_add_b2_avatar_url_to_userprofile'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='userprofile',
            name='avatar',
        ),
        migrations.RenameField(
            model_name='userprofile',
            old_name='b2_avatar_url',
            new_name='avatar_url',
        ),
        migrations.AddField(
            model_name='userprofile',
            name='avatar_source',
            field=models.CharField(
                choices=[
                    ('default', 'Default (letter gradient)'),
                    ('direct', 'Direct upload'),
                    ('google', 'Google social sign-in'),
                    ('facebook', 'Facebook social sign-in'),
                    ('apple', 'Apple social sign-in'),
                ],
                db_index=True,
                default='default',
                help_text='Origin of the avatar_url value.',
                max_length=20,
            ),
        ),
    ]
