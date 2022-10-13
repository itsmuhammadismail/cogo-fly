# Generated by Django 3.0.6 on 2022-04-02 07:35

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('seo', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='appstatus',
            old_name='users_aountcreation',
            new_name='users_acounts_creation',
        ),
        migrations.AlterField(
            model_name='appstatus',
            name='date',
            field=models.DateField(default=datetime.datetime(2022, 4, 2, 7, 35, 42, 938868, tzinfo=utc)),
        ),
        migrations.AlterField(
            model_name='pagenbvisites',
            name='creation_date',
            field=models.DateTimeField(default=datetime.datetime(2022, 4, 2, 7, 35, 42, 938868, tzinfo=utc)),
        ),
    ]
