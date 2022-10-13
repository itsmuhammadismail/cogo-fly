from django.db import models
from django.utils.timezone import now


class AppStatus(models.Model):
    date = models.DateField(default=now())
    users_acounts_creation = models.IntegerField(default=0)
    users_profils_acount = models.IntegerField(default=0)
    completed_users_profils_count = models.IntegerField(default=0)
    daily_users_message_count = models.IntegerField(default=0)
    total_users_messages_count = models.IntegerField(default=0)
    users_connected_count = models.IntegerField(default=0)
    users_guest_count = models.IntegerField(default=0)
    users_profils_count_by_profil_hadicap = models.IntegerField(default=0)
    daily_trips_added = models.IntegerField(default=0)
    total_trips_added = models.IntegerField(default=0)
    pictures_count = models.IntegerField(default=0)
    daily_searches_count = models.IntegerField(default=0)
    total_searches_count = models.IntegerField(default=0)
    counter_nb_visites_total = models.IntegerField(default=0)
    counter_nb_visites_today = models.IntegerField(default=0)


class PageNbVisites(models.Model):
    url = models.URLField()
    nb_visites = models.IntegerField(default=1)
    created = models.DateTimeField(default=now())

    def __str__(self):
        return self.url
