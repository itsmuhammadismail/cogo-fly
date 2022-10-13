# Generated by Django 3.0.6 on 2022-03-31 18:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cogofly', '0011_auto_20220331_2030'),
    ]

    operations = [
        migrations.RenameField(
            model_name='profile',
            old_name='I_have_an_handicap',
            new_name='handicap',
        ),
        migrations.RemoveField(
            model_name='privacy',
            name='help_hukranians',
        ),
        migrations.AddField(
            model_name='privacy',
            name='help_hukranian',
            field=models.BooleanField(default=False, verbose_name='help hukranian'),
        ),
    ]
