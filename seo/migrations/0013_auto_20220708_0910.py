# Generated by Django 3.0.6 on 2022-07-08 07:10

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('seo', '0012_auto_20220402_1109'),
    ]

    operations = [
        migrations.AlterField(
            model_name='appstatus',
            name='date',
            field=models.DateField(default=datetime.datetime(2022, 7, 8, 7, 10, 1, 137100, tzinfo=utc)),
        ),
        migrations.AlterField(
            model_name='pagenbvisites',
            name='created',
            field=models.DateTimeField(default=datetime.datetime(2022, 7, 8, 7, 10, 1, 138098, tzinfo=utc)),
        ),
    ]