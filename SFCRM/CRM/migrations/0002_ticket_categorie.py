# Generated by Django 5.0.4 on 2024-05-15 16:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('CRM', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='ticket',
            name='Categorie',
            field=models.BooleanField(default=False),
        ),
    ]
