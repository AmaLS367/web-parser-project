from django.core.management.base import BaseCommand
from parsers.sites_parsers import run_all_parsers

class Command(BaseCommand):
    help = 'Запуск всех парсеров'

    def handle(self, *args, **kwargs):
        run_all_parsers()
