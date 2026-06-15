from django.core.management.base import BaseCommand

from portal.services import start_scrape_job


class Command(BaseCommand):
    help = "Ejecuta scraping desde terminal (igual que el dashboard)"

    def add_arguments(self, parser):
        parser.add_argument("--country", default="all")
        parser.add_argument("--site", default="all")
        parser.add_argument("--max-products", type=int, default=50)
        parser.add_argument("--max-pages", type=int, default=3)
        parser.add_argument("--export", action="store_true")

    def handle(self, *args, **options):
        from portal.models import ScrapeJob

        job = start_scrape_job(
            country=options["country"],
            site_slug=options["site"],
            max_pages=options["max_pages"],
            max_products=options["max_products"],
            do_export=options["export"],
        )
        if not job:
            self.stderr.write("Ya hay un job en curso.")
            return
        self.stdout.write(f"Job #{job.pk} iniciado. Esperando…")
        import time

        while True:
            job.refresh_from_db()
            if job.status != ScrapeJob.Status.RUNNING:
                break
            time.sleep(2)
        self.stdout.write(job.log)
        if job.error_message:
            self.stderr.write(job.error_message)
