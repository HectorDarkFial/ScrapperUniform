from django.core.management.base import BaseCommand

from portal.services import import_sites_from_yaml


class Command(BaseCommand):
    help = "Importa tiendas desde config/sites/*.yaml a la base Django"

    def handle(self, *args, **options):
        n = import_sites_from_yaml()
        self.stdout.write(self.style.SUCCESS(f"Importadas/actualizadas {n} tiendas."))
