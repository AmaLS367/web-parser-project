#parsers.sites_parsers.py
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
import time
from datetime import datetime, timedelta
from parsers.padel39_parser import run_once as padel39_run_once
from parsers.padelclubaustin_runner import run_once as padelclubaustin_run_once
from parsers.the_king_of_padel_parser import parse_slots as the_king_of_padel_parse_slots
from parsers.Upadel_parser import main as upadel_run_once

def safe_run(parser_func, site_name):
    print("\n========================================")
    print(f"Парсинг сайта: {site_name}")
    print("========================================")
    try:
        parser_func()
    except Exception as e:
        print(f"\nОшибка при парсинге {site_name}: {e}")
        print(f"Парсинг сайта {site_name} недоступен.")

def run_all_parsers():
    print("Запуск парсинга всех сайтов...\n")
    safe_run(padel39_run_once, "Padel39")
    safe_run(padelclubaustin_run_once, "Padel Club Austin")
    safe_run(the_king_of_padel_parse_slots, "The King of Padel")
    safe_run(upadel_run_once, "Upadel")

if __name__ == "__main__":
    while True:
        run_all_parsers()
        next_run_time = datetime.now() + timedelta(hours=4)
        print(f"\nСледующий парсинг будет в {next_run_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("Ожидание 4 часа до следующего запуска...\n")
        time.sleep(4 * 60 * 60)  # 4 часа * 60 минут * 60 секунд
