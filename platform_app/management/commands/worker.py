from django.core.management.base import BaseCommand
from platform_app.jobs import seed_profile, worker


class Command(BaseCommand):
    help = "Process queued PDF reviews. Run exactly one worker for the initial deployment."

    def handle(self, *args, **options):
        seed_profile()
        worker()
