# parsers/padelclubaustin_parser.py

from datetime import datetime, timedelta, time as dt_time
import time
import random
import requests
from bs4 import BeautifulSoup
from .base_parser import BaseParser
from core.models import Slot
import os 
from dotenv import load_dotenv

load_dotenv()

class PadelClubAustinParser(BaseParser):
    SITE_NAME = "Padel Club Austin"

    base_url = "https://book.padelclubaustin.com"
    login_url = base_url + "/users/sign_in"
    api_url = base_url + "/api/facilities/674/available_hours"

    email = os.getenv("PADELCLUBAUSTIN_EMAIL")
    password = os.getenv("PADELCLUBAUSTIN_PASSWORD")

    groups = {
        'A': {'surface': 'padel_outdoor_a', 'name': 'Padel indoor A'},
        'B': {'surface': 'padel_outdoor_b', 'name': 'Padel indoor B'}
    }

    # заголовки для HTML (логин)
    login_headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    # заголовки для JSON API
    api_headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "X-Requested-With": "XMLHttpRequest",
    }

    def get_auth_token(self, session):
        try:
            resp = session.get(self.login_url, headers=self.login_headers)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'html.parser')
            tag = soup.find('meta', {'name': 'csrf-token'})
            return tag['content'] if tag else None
        except Exception as e:
            self.handle_error(f"get_auth_token: {e}")
            return None

    def login(self, session):
        for _ in range(3):
            token = self.get_auth_token(session)
            if not token:
                continue
            data = {
                'authenticity_token': token,
                'user[email]': self.email,
                'user[password]': self.password,
                'user[remember_me]': '0'
            }
            hdrs = self.login_headers.copy()
            hdrs.update({
                "Content-Type": "application/x-www-form-urlencoded",
                "Origin": self.base_url,
                "Referer": self.login_url
            })
            time.sleep(random.uniform(1,3))
            r = session.post(self.login_url, data=data, headers=hdrs)
            if 'sign_out' in r.text:
                return True
        self.handle_error("login: failed after 3 attempts")
        return False

    def fetch_slots(self, session, surface, date_obj):
        try:
            ts = int(datetime.combine(date_obj, dt_time.min).timestamp())
            params = {'timestamp': ts, 'surface': surface, 'kind': 'reservation'}
            r = session.get(self.api_url, params=params, headers=self.api_headers)
            r.raise_for_status()
            data = r.json()
            hours = data.get('available_hours', [])
        except Exception as e:
            self.handle_error(f"fetch_slots: {e}")
            return []

        slots = []
        for item in hours:
            if item.get('available'):
                sched = item.get('schedule')
                shift = item.get('shift', '').strip()
                slots.append((sched, shift))
        return slots

    @staticmethod
    def parse_time_range(shift):
        import re
        from datetime import datetime as dt_cls

        core = shift.strip().split()[0].lower()
        parts = core.split('-', 1)
        if len(parts) != 2 or not re.search(r'(am|pm)$', parts[1]):
            raise ValueError(f"invalid time format: {shift}")

        start, end = parts
        # добавляем am/pm из конца, если нужно
        if not re.search(r'(am|pm)$', start):
            ampm = re.search(r'(am|pm)$', end).group(1)
            start += ampm

        fmt1 = '%I:%M%p' if ':' in start else '%I%p'
        fmt2 = '%I:%M%p' if ':' in end else '%I%p'

        return dt_cls.strptime(start, fmt1).time(), dt_cls.strptime(end, fmt2).time()

    def parse_slots(self, raw_list, date_obj, court_name):
        parsed = []
        for sched, shift in raw_list:
            # если нет дефиса — сохраняем только raw_shift
            if '-' not in shift:
                parsed.append(Slot(
                    booking_site=self.site,
                    date=date_obj,
                    start_time=None,
                    end_time=None,
                    is_available=True,
                    court=court_name,
                    raw_shift=shift
                ))
                continue

            try:
                start, end = self.parse_time_range(shift)
                parsed.append(Slot(
                    booking_site=self.site,
                    date=date_obj,
                    start_time=start,
                    end_time=end,
                    is_available=True,
                    court=court_name,
                    raw_shift=shift
                ))
            except Exception as e:
                self.handle_error(f"parse_slots: '{shift}' → {e}")
                # и снова сохраняем в виде raw_shift
                parsed.append(Slot(
                    booking_site=self.site,
                    date=date_obj,
                    start_time=None,
                    end_time=None,
                    is_available=True,
                    court=court_name,
                    raw_shift=shift
                ))
        return parsed

    def parse(self, days=6):
        self.slots = []
        self.last_error = None
        start_ts = time.time()

        with requests.Session() as session:
            if not self.login(session):
                return False

            today = datetime.now().date()
            for i in range(days):
                d = today + timedelta(days=i)
                for cfg in self.groups.values():
                    raw = self.fetch_slots(session, cfg['surface'], d)
                    self.slots.extend(self.parse_slots(raw, d, cfg['name']))

        self.duration = time.time() - start_ts
        return True


def run_once():
    return PadelClubAustinParser().run_once()
