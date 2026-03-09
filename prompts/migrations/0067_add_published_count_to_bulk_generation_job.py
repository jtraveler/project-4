from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('prompts', '0066_add_gpt_image_1_generator_choice'),
    ]

    operations = [
        migrations.AddField(
            model_name='bulkgenerationjob',
            name='published_count',
            field=models.PositiveIntegerField(default=0),
        ),
    ]
