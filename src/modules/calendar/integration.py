from ics import Calendar, Event
from datetime import datetime, timedelta
import os

class CalendarManager:
    def __init__(self):
        self.calendar = Calendar()
        self.filename = "data/entrevistas.ics"
        self._load()

    def _load(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r') as f:
                    self.calendar = Calendar(f.read())
            except:
                pass

    def add_event(self, title, description, start_time, duration_minutes=60):
        e = Event()
        e.name = title
        e.description = description
        e.begin = start_time
        e.duration = timedelta(minutes=duration_minutes)
        self.calendar.events.add(e)
        self._save()
        return self.filename

    def _save(self):
        os.makedirs("data", exist_ok=True)
        with open(self.filename, 'w') as f:
            f.writelines(self.calendar)
