from django.db import transaction
from django.utils import timezone
from core.models import BookingSite, Slot, ParserStatus


class BaseParser:
    SITE_NAME = "Без названия"  # Переопределять в дочерних классах

    def __init__(self):
        # создаём или получаем запись о сайте
        self.site = BookingSite.objects.get_or_create(name=self.SITE_NAME)[0]
        self.slots = []
        self.last_error = None
        self.start_time = None
        self.duration = 0

    @transaction.atomic
    def save_to_db(self):
        """Массовое обновление слотов: удаляем старые, создаём новые."""
        Slot.objects.filter(booking_site=self.site).delete()
        Slot.objects.bulk_create(self.slots, batch_size=500)

    def update_status(self, is_success=True):
        """Обновить ParserStatus для сайта."""
        ParserStatus.objects.update_or_create(
            booking_site=self.site,
            defaults={
                'status': 'success' if is_success else 'error',
                'message': self.last_error or "",
                'duration': self.duration,
                'checked_at': timezone.now()
            }
        )

    def parse(self):
        """Должен быть переопределён в дочерних классах."""
        raise NotImplementedError("Метод parse() должен быть реализован")

    def handle_error(self, error):
        """Логируем ошибку и сохраняем текст для статуса."""
        self.last_error = str(error)
        print(f"[{self.SITE_NAME}] Ошибка: {self.last_error}")

    def run_once(self):
        """Запустить parse(), обновить статус, сохранить слоты и вывести итог."""
        print(f"→ [{self.SITE_NAME}] Запуск парсера...")
        self.start_time = timezone.now()
        success = False

        try:
            success = self.parse()
            if success is None:
                success = True
        except Exception as e:
            self.handle_error(e)

        finally:
            self.duration = (timezone.now() - self.start_time).total_seconds()
            # Обновляем статус (до сохранения слотов, чтобы видеть даже пустой результат)
            self.update_status(is_success=success)

            if success and self.slots:
                self.save_to_db()

            # Итоговый вывод
            print(f"→ [{self.SITE_NAME}] Завершено. Успех: {success}")
            print(f"→ Найдено слотов: {len(self.slots)}")

        return {
            "success": success,
            "slots": self.slots,
            "duration": self.duration,
            "error": self.last_error or ""
        }
