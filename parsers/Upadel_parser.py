# parsers/upadel_parser.py

import time
import random
import re
import requests
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from .base_parser import BaseParser
from core.models import Slot


class UpadelParser(BaseParser):
    SITE_NAME = "Upadel"

    LOGIN_URL = "https://book.upadel.us/users/sign_in"
    AVAILABILITY_URL = "https://book.upadel.us/api/facilities/527/available_hours"

    EMAIL = "levonlevonyanxx@gmail.com"
    PASSWORD = "Project129!"

    GROUPS = {
        'a': {'surface': 'padel_indoor_a', 'name': 'Padel indoor A'},
        'b': {'surface': 'padel_indoor_b', 'name': 'Padel indoor B'}
    }

    HEADERS_HTML = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/136.0.0.0 Safari/537.36",
        "Referer": "https://book.upadel.us/book/upadelwoodlands"
    }
    HEADERS_API = {
        **HEADERS_HTML,
        "X-Requested-With": "XMLHttpRequest",
        "Accept": "application/json"
    }

    def get_token(self, session):
        resp = session.get(self.LOGIN_URL, headers=self.HEADERS_HTML)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
        tag = soup.find('input', {'name': 'authenticity_token'})
        if not tag:
            raise ValueError("Не найден authenticity_token")
        return tag['value']

    def login(self, session):
        token = self.get_token(session)
        data = {
            'authenticity_token': token,
            'user[email]': self.EMAIL,
            'user[password]': self.PASSWORD,
            'user[remember_me]': '1',
            'commit': 'Log in'
        }
        hdrs = self.HEADERS_HTML.copy()
        hdrs['Referer'] = self.LOGIN_URL
        resp = session.post(self.LOGIN_URL, data=data, headers=hdrs)
        resp.raise_for_status()
        if "Invalid Email or password" in resp.text:
            raise ValueError("Авторизация не удалась")
        return True

    def fetch_group_slots(self, session, group_key, date_obj):
        now = datetime.now()
        ts = int(now.timestamp()) if date_obj == now.date() else int(datetime.combine(date_obj, datetime.min.time()).timestamp())

        params = {
            'timestamp': ts,
            'surface': self.GROUPS[group_key]['surface'],
            'kind': 'reservation'
        }
        resp = session.get(self.AVAILABILITY_URL, headers=self.HEADERS_API, params=params)
        resp.raise_for_status()
        return resp.json().get('available_hours', [])

    def parse_time_range(self, sched):
        s = sched.strip().lower()

        # Форматы вида "6-6:30am", "6:30-7am", "7:00-8:00pm"
        match = re.match(r'(\d{1,2}(?::\d{2})?)[-–](\d{1,2}(?::\d{2})?)(am|pm)', s)
        if not match:
            raise ValueError(f"Invalid time range format: {sched}")
        start_str, end_str, meridiem = match.groups()

        fmt_start = "%I:%M%p" if ':' in start_str else "%I%p"
        fmt_end = "%I:%M%p" if ':' in end_str else "%I%p"

        start_time = datetime.strptime(start_str + meridiem, fmt_start).time()
        end_time = datetime.strptime(end_str + meridiem, fmt_end).time()

        return start_time, end_time

    def parse(self, days=7):
        self.slots = []
        self.last_error = None
        start_ts = time.time()

        with requests.Session() as session:
            session.headers.update(self.HEADERS_HTML)
            try:
                self.login(session)
            except Exception as e:
                self.handle_error(e)
                return False

            today = datetime.now().date()
            for delta in range(days):
                date_obj = today + timedelta(days=delta)
                for grp_key, cfg in self.GROUPS.items():
                    time.sleep(random.uniform(1.0, 2.5))
                    try:
                        raw = self.fetch_group_slots(session, grp_key, date_obj)
                    except Exception as e:
                        self.handle_error(f"{cfg['name']} {date_obj} fetch error: {e}")
                        continue

                    for item in raw:
                        if not item.get('available'):
                            continue
                        sched = item.get('schedule')
                        try:
                            # Основной способ: сначала пробуем HH:MM:SS
                            try:
                                start_time = datetime.strptime(sched, "%H:%M:%S").time()
                                duration = item.get('duration', 60)
                                end_dt = datetime.combine(datetime.today(), start_time) + timedelta(minutes=duration)
                                end_time = end_dt.time()
                            except ValueError:
                                # Альтернатива: диапазон, например "6-6:30am"
                                start_time, end_time = self.parse_time_range(sched)
                        except Exception as e:
                            self.handle_error(f"{cfg['name']} parse time error: {sched}")
                            continue

                        price_raw = item.get('price')
                        try:
                            price = float(str(price_raw).split()[0]) if price_raw else None
                        except:
                            price = None

                        self.slots.append(
                            Slot(
                                booking_site=self.site,
                                date=date_obj,
                                start_time=start_time,
                                end_time=end_time,
                                is_available=True,
                                price=price,
                                court=cfg['name']
                            )
                        )

        self.duration = time.time() - start_ts
        return True


def run_once():
    parser = UpadelParser()
    return parser.run_once()
