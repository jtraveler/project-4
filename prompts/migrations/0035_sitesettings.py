# Generated manually for SiteSettings model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('prompts', '0034_prompt_prompt_ai_gen_idx_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='SiteSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('auto_approve_comments', models.BooleanField(
                    default=True,
                    help_text='Automatically approve new comments (disable for manual moderation)'
                )),
            ],
            options={
                'verbose_name': 'Site Settings',
                'verbose_name_plural': 'Site Settings',
            },
        ),
    ]
