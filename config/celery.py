import os
from celery import Celery
from django.conf import settings

# Устанавливаем переменную окружения для Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Создаём экземпляр приложения Celery
app = Celery('config')

# Загружаем конфигурацию Celery из настроек Django
app.config_from_object('django.conf:settings', namespace='CELERY')

# Автоматически ищем задачи в файлах tasks.py установленных приложений
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
