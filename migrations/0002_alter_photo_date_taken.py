# Generated by Django 4.1.1 on 2022-09-14 11:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('photo_elixir', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='photo',
            name='date_taken',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
