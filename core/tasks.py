# core/tasks.py
from celery import shared_task
from django.utils import timezone
from core.models import BookingSite, ParserStatus
from parsers.padel39_parser import main as padel39_run_once
from parsers.Upadel_parser import run_once as upadel_run_once
from parsers.padelclubaustin_runner import run_once as padelclubaustin_run_once
from parsers.the_king_of_padel_parser import main as kingofpadel_run_once

PARSER_MAPPING = {
    "padel39": padel39_run_once,
    "upadel": upadel_run_once,
    "padel club austin": padelclubaustin_run_once,
    "the king of padel": kingofpadel_run_once,
}

@shared_task(bind=True, name='core.parse_all_sites', ignore_result=True)
def parse_all_sites(self):
    """Celery task: парсинг всех активных сайтов"""
    active_sites = BookingSite.objects.filter(is_active=True)
    if not active_sites.exists():
        print("Нет активных сайтов для парсинга")
        return "Нет активных сайтов"

    for site in active_sites:
        print(f"\nЗапускаем парсер для сайта: {site.name}")
        parser_func = PARSER_MAPPING.get(site.name.lower())
        if not parser_func:
            msg = f"Парсер для сайта '{site.name}' не найден. Пропускаем."
            print(msg)
            ParserStatus.objects.update_or_create(
                booking_site=site,
                defaults={
                    'status': 'parser_not_found',
                    'message': msg,
                    'checked_at': timezone.now()
                }
            )
            continue

        try:
            result = parser_func()
            if not isinstance(result, dict):
                raise ValueError("Результат парсера должен быть словарём")

            if 'status' in result and 'total_slots' in result:
                success = result['status'] == 'success'
                total = result['total_slots']
                message = f"Всего слотов: {total}"
                parsed_slots = total
                duration = result.get('duration')
            else:
                success = result.get('success', False)
                slots = result.get('slots', []) or []
                parsed_slots = len(slots)
                message = result.get('error', '') if not success else f"Успешно обработано слотов: {parsed_slots}"
                duration = result.get('duration', None)

            status_code = 'success' if success else 'error'
            ParserStatus.objects.update_or_create(
                booking_site=site,
                defaults={
                    'status': status_code,
                    'message': message,
                    'duration': duration,
                    'checked_at': timezone.now()
                }
            )
            print(f"[{site.name}] {message}")

        except Exception as e:
            error_msg = f"Критическая ошибка при парсинге сайта '{site.name}': {e}"
            print(error_msg)
            ParserStatus.objects.update_or_create(
                booking_site=site,
                defaults={
                    'status': 'critical_error',
                    'message': error_msg,
                    'checked_at': timezone.now()
                }
            )

    print("\nПарсинг всех сайтов завершён")
    return "Парсинг завершен"
