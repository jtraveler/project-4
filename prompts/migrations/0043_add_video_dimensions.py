# Generated manually for Phase M5: Video Dimensions (Layout Shift Fix)

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('prompts', '0042_add_needs_seo_review'),
    ]

    operations = [
        migrations.AddField(
            model_name='prompt',
            name='video_width',
            field=models.PositiveIntegerField(
                blank=True,
                null=True,
                help_text='Video width in pixels (extracted during upload)'
            ),
        ),
        migrations.AddField(
            model_name='prompt',
            name='video_height',
            field=models.PositiveIntegerField(
                blank=True,
                null=True,
                help_text='Video height in pixels (extracted during upload)'
            ),
        ),
    ]
