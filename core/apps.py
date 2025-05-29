from django.apps import AppConfig
from django.db.utils import OperationalError, ProgrammingError
import sys

class CoreConfig(AppConfig):
    name = 'core'

    def ready(self):
        # Только при запуске сервера
        if 'runserver' not in sys.argv and 'gunicorn' not in sys.argv:
            return

        try:
            from django_celery_beat.models import PeriodicTask, IntervalSchedule

            # Создаём интервал 4 часа (если нет)
            interval, _ = IntervalSchedule.objects.get_or_create(
                every=4,
                period=IntervalSchedule.HOURS
            )

            # Удаляем старую задачу (если она есть)
            PeriodicTask.objects.filter(task='core.parse_all_sites').delete()

            # Создаём новую задачу
            PeriodicTask.objects.create(
                name='All sites parsing',
                task='core.parse_all_sites',
                interval=interval,
                enabled=True
            )

        except (ImportError, OperationalError, ProgrammingError) as e:
            # Пропускаем, если БД ещё не готова (например, при миграциях)
            print(f'[PeriodicTask setup skipped] {e}')
