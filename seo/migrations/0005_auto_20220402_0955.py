# Generated by Django 3.0.6 on 2022-04-02 07:55

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('seo', '0004_auto_20220402_0943'),
    ]

    operations = [
        migrations.RenameField(
            model_name='appstatus',
            old_name='users_messages_count',
            new_name='daily_users_message_count',
        ),
        migrations.AddField(
            model_name='appstatus',
            name='total_users_messages_count',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='appstatus',
            name='date',
            field=models.DateField(default=datetime.datetime(2022, 4, 2, 7, 55, 3, 570751, tzinfo=utc)),
        ),
        migrations.AlterField(
            model_name='pagenbvisites',
            name='creation_date',
            field=models.DateTimeField(default=datetime.datetime(2022, 4, 2, 7, 55, 3, 570751, tzinfo=utc)),
        ),
    ]