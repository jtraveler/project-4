# Generated by Django 5.2.3 on 2025-06-20 09:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('prompts', '0005_prompt_slug_prompt_status_alter_comment_created_on'),
    ]

    operations = [
        migrations.AlterField(
            model_name='comment',
            name='created_on',
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='prompt',
            name='slug',
            field=models.SlugField(max_length=200, unique=True),
        ),
    ]
