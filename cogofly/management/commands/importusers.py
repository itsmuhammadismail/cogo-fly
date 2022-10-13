import csv

from cogofly.models import Profile, User
from django.db.utils import IntegrityError
from django.core.management.base import BaseCommand, CommandError

USER_KEYS = ['first_name', 'last_name', 'email', 'password', 'date_joined']

class Command(BaseCommand):
    help = 'Closes the specified poll for voting'

    def add_arguments(self, parser):
        parser.add_argument('csv_path', type=str)

    def handle(self, *args, **options):
        reader = csv.DictReader(open(options['csv_path']))
        for line in reader:
            try:
                User.objects.create(**{k: v for k, v in line.items() if k in USER_KEYS}, is_active=False)
            except IntegrityError:
                pass