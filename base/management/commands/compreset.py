from django.core.management.base import BaseCommand, CommandError
from base import models
from django.contrib.auth.models import User


class Command(BaseCommand):
    def handle(self, *args, **options):
        models.Team.objects.all().delete()
        User.objects.exclude(is_superuser=True).delete()
        models.ArchivedEmail.objects.all().delete()
        self.stdout.write("Competition reset performed")
