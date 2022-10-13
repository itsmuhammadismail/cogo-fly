import time
from django.core.management.base import BaseCommand
from cogofly.models import Picture, User, Profile, Message, Trip, Search
from cogofly.utils import send_mail
from seo.models import AppStatus, PageNbVisites
from django.utils.timezone import now


class Command(BaseCommand):
    help = "Closes the specified poll for voting"

    def handle(self, *args, **options):
        daily_users_acounts_creation = User.objects.filter(created=now().date()).count()
        daily_users_profils_acount_creation = Profile.objects.count()
        daily_users_profils_completed_acount_creation = Profile.objects.filter(
            is_completed=True
        ).count()
        daily_users_message_count = Message.objects.filter(created=now().date()).count()
        total_users_messages_count = Message.objects.count()
        daily_users_connected_count = User.objects.filter(is_active=True).count()
        daily_users_guest_count = User.objects.filter(is_active=False).count()
        daily_users_profils_count_by_profil_hadicap = Profile.objects.filter(
            handicap=True
        ).count()
        daily_trips_added = Trip.objects.filter(created=now().date()).count()
        total_trips_added = Trip.objects.count()
        counter_nb_visites_total = PageNbVisites.objects.count()
        counter_nb_visites_today = PageNbVisites.objects.filter(created=now().date()).count()
        pictures_count = Picture.objects.count()
        daily_searches_count = Search.objects.filter(created=now().date()).count()
        total_searches_count = Search.objects.count()

        app_status = AppStatus.objects.create(
            users_acounts_creation=daily_users_acounts_creation,
            users_profils_acount=daily_users_profils_acount_creation,
            completed_users_profils_count=daily_users_profils_completed_acount_creation,
            daily_users_message_count=daily_users_message_count,
            total_users_messages_count=total_users_messages_count,
            users_connected_count=daily_users_connected_count,
            users_guest_count=daily_users_guest_count,
            users_profils_count_by_profil_hadicap=daily_users_profils_count_by_profil_hadicap,
            daily_trips_added=daily_trips_added,
            total_trips_added=total_trips_added,
            pictures_count=pictures_count,
            daily_searches_count=daily_searches_count,
            total_searches_count=total_searches_count,
            counter_nb_visites_total=counter_nb_visites_total,
            counter_nb_visites_today=counter_nb_visites_today,
        )
        app_status.save()

        time.sleep(1)
        emails = [
            "cogofly@gmail.com",
            "nuno.ricardo.mars@gmail.com",
        ]
        for email in emails:
            send_mail(
                email,
                "SEO - Statistiques du jour",
                "seo/email/seo_statistiques_du_jour.html",
                {
                    "counter_nb_visites_total": counter_nb_visites_total,
                    "counter_nb_visites_today": counter_nb_visites_today,
                    "app_status": app_status,
                },
            )
