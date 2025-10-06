# Migration to replace AWS Rekognition with OpenAI Vision API
# Adds new fields to ModerationLog and updates service choices

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('prompts', '0020_alter_moderationlog_service_profanityword'),
    ]

    operations = [
        # Add new fields to ModerationLog
        migrations.AddField(
            model_name='moderationlog',
            name='severity',
            field=models.CharField(
                choices=[
                    ('low', 'Low'),
                    ('medium', 'Medium'),
                    ('high', 'High'),
                    ('critical', 'Critical'),
                ],
                default='medium',
                help_text='Severity of violations detected',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='moderationlog',
            name='explanation',
            field=models.TextField(
                blank=True,
                help_text='AI explanation of moderation decision',
            ),
        ),
        # Update service choices to replace Rekognition/Cloudinary with OpenAI Vision
        migrations.AlterField(
            model_name='moderationlog',
            name='service',
            field=models.CharField(
                choices=[
                    ('profanity', 'Custom Profanity Filter'),
                    ('openai', 'OpenAI Moderation API'),
                    ('openai_vision', 'OpenAI Vision API'),
                ],
                help_text='Which AI moderation service was used',
                max_length=50,
            ),
        ),
    ]
