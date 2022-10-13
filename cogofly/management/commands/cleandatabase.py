from cogofly.models import Profile, User

from django.core.management.base import BaseCommand




class Command(BaseCommand):
    help = 'Del user whitout profile'


    def handle(self, *args, **options):
        users = User.objects.all()
        for user in users:
            if user.email == ' ' or user.email is None:
                user.delete()

        profils = Profile.objects.all()
        for profil in profils:
            if profil.user.email is None or profil.user.email == ' ' or profil is None:
                profil.delete()