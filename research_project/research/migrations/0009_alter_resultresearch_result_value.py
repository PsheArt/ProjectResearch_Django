# Generated by Django 4.1.4 on 2024-11-28 09:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('research', '0008_remove_resultresearch_aspect'),
    ]

    operations = [
        migrations.AlterField(
            model_name='resultresearch',
            name='result_value',
            field=models.TextField(null=True),
        ),
    ]
