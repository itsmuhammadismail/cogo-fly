# Generated by Django 3.0.6 on 2022-03-28 19:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cogofly', '0009_auto_20220322_2017'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='I_have_an_handicap',
            field=models.BooleanField(default=False, verbose_name='I have a handicap'),
        ),
        migrations.AddField(
            model_name='profile',
            name='help_ukranian',
            field=models.BooleanField(default=False, verbose_name='Help Ukranian'),
        ),
        migrations.AddField(
            model_name='search',
            name='I_have_an_handicap',
            field=models.BooleanField(default=False, verbose_name='I have a handicap'),
        ),
        migrations.AddField(
            model_name='search',
            name='help_ukranian',
            field=models.BooleanField(default=False, verbose_name='Help Ukranian'),
        ),
    ]
