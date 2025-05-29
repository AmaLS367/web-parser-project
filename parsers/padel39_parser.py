# padel39_parser.py
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

API_URL = "https://playtomic.com/api/clubs/availability"
TENANT_ID = "dab6076a-baf6-48ca-af21-d9ada2345290"
SPORT_ID = "PADEL"


def init_session():
    session = requests.Session()
    # Получаем необходимые cookies
    resp = session.get("https://playtomic.com/clubs/padel39")
    resp.raise_for_status()
    session.headers.update({
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://playtomic.com/clubs/padel39",
        "Origin": "https://playtomic.com",
        "X-Requested-With": "XMLHttpRequest",
    })
    return session


def fetch_availability(session, date):
    params = {
        "tenant_id": TENANT_ID,
        "sport_id": SPORT_ID,
        "date": date.isoformat()
    }
    resp = session.get(API_URL, params=params)
    resp.raise_for_status()
    return resp.json()  # возвращает список словарей


def parse_and_save(data_list, date, booking_site):
    count = 0
    for court_info in data_list:
        court_name = court_info.get('resource_id') or 'Unknown Court'
        for slot in court_info.get('slots', []):
            try:
                # Начало и длительность
                start_str = slot.get('start_time')  # '12:30:00' или '12:30'
                # Поддержка разных форматов
                fmt = "%H:%M:%S" if start_str.count(':') == 2 else "%H:%M"
                start_time = datetime.strptime(start_str, fmt).time()

                duration = slot.get('duration', 0)
                end_time = (datetime.combine(date, start_time) + timedelta(minutes=duration)).time()

                # Цена как Decimal
                price_str = slot.get('price', '') or '0'
                price = Decimal(price_str.split()[0]) if price_str else Decimal('0')

                # Обновляем или создаём
                Slot.objects.update_or_create(
                    booking_site=booking_site,
                    date=date,
                    start_time=start_time,
                    end_time=end_time,
                    court=court_name,
                    defaults={
                        'is_available': True,
                        'price': price,
                    }
                )
                count += 1
            except Exception as e:
                print(f"Error saving slot for {date}: {e}")
    return count


def main():
    session = init_session()
    today = datetime.today().date()
    dates = [today + timedelta(days=i) for i in range(5)]

    booking_site, _ = BookingSite.objects.get_or_create(name="Padel39")
    total_slots = 0

    for date in dates:
        try:
            data_list = fetch_availability(session, date)
            count = parse_and_save(data_list, date, booking_site)
            print(f"Parsed and saved {count} slots for {date}")
            total_slots += count
            time.sleep(1)
        except Exception as e:
            print(f"Error fetching availability for {date}: {e}")

    return {"status": "success", "total_slots": total_slots}