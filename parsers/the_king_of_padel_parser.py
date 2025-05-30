# parsers/the_king_of_padel_parser.py

import os
import django
import time
import requests
from datetime import datetime, timedelta
from decimal import Decimal

# Django setup
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from core.models import Slot, BookingSite

API_URL       = "https://playtomic.com/api/clubs/availability"
TENANT_ID     = "023c0c73-1597-42e9-aa6d-8756c0c694aa"
SPORT_ID      = "PADEL"
CLUB_URLS     = [
    "https://playtomic.com/clubs/the-king-of-padel-sd",
    "https://playtomic.com/clubs/the-king-of-padel-sa"
]

def init_session():
    """Инициализируем requests.Session с нужными cookies и заголовками."""
    session = requests.Session()
    for url in CLUB_URLS:
        try:
            r = session.get(url)
            r.raise_for_status()
        except Exception as e:
            print(f"[The King of Padel] Warning: не удалось получить cookies с {url}: {e}")
    session.headers.update({
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json, text/plain, */*",
        "Referer": CLUB_URLS[0],
        "Origin": "https://playtomic.com",
        "X-Requested-With": "XMLHttpRequest",
    })
    return session

def fetch_availability(session, date):
    """Делаем GET к API и возвращаем Python-структуру."""
    params = {
        "tenant_id": TENANT_ID,
        "sport_id": SPORT_ID,
        "date": date.isoformat()
    }
    r = session.get(API_URL, params=params)
    r.raise_for_status()
    return r.json()  # Согласно документации — список словарей

def parse_and_save(data_list, date, booking_site):
    """
    Разбираем data_list (список dict) и сохраняем слоты в БД.
    Возвращаем число успешно сохранённых слотов.
    """
    count = 0
    # Для дебага можно раскомментировать:
    # print(f"[The King of Padel] DEBUG {date}: получено {len(data_list)} элементов")
    # print(data_list[:1])

    for court_info in data_list:
        court_name = court_info.get("resource_id") or court_info.get("name") or "Unknown Court"
        slots_key = "slots" if "slots" in court_info else "available_hours"
        for slot in court_info.get(slots_key, []):
            try:
                # start_time
                start_str = slot.get("start_time")
                fmt = "%H:%M:%S" if start_str and start_str.count(":") == 2 else "%H:%M"
                start_t = datetime.strptime(start_str, fmt).time()

                # end_time
                duration = slot.get("duration", 60)
                end_t = (datetime.combine(date, start_t) + timedelta(minutes=duration)).time()

                # price
                price_raw = slot.get("price", "0")
                price = Decimal(str(price_raw).split()[0]) if price_raw else Decimal("0")

                Slot.objects.update_or_create(
                    booking_site=booking_site,
                    date=date,
                    start_time=start_t,
                    end_time=end_t,
                    court=court_name,
                    defaults={
                        "is_available": True,
                        "price": price,
                    }
                )
                count += 1

            except Exception as e:
                # Если нужна отладка, можно print(e) или logger.warning
                print(f"[The King of Padel] Ошибка при сохранении слота {date} {court_name}: {e}")

    return count

def main():
    session = init_session()
    today = datetime.today().date()
    days = 28  # сколько дней парсить
    booking_site, _ = BookingSite.objects.get_or_create(name="The King of Padel")

    total = 0
    start_ts = time.time()

    for offset in range(days):
        date = today + timedelta(days=offset)
        try:
            data_list = fetch_availability(session, date)
            cnt = parse_and_save(data_list, date, booking_site)
            print(f"[The King of Padel] Parsed {cnt} slots for {date}")
            total += cnt
        except Exception as e:
            print(f"[The King of Padel] Error fetching availability for {date}: {e}")

        # Небольшая пауза, чтобы не перегружать сервер
        time.sleep(0.5)

    duration = time.time() - start_ts
    return {
        "status": "success",
        "total_slots": total,
        "duration": duration,
        "error": None
    }