# Generated by Django 4.1.4 on 2024-11-28 09:32

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('research', '0007_remove_rating_result_alter_rating_score_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='resultresearch',
            name='aspect',
        ),
    ]
