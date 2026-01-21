import json
import os
from typing import Dict, List, Any
from src.core.models import CandidateProfile, Application

DATA_DIR = "data"
PROFILE_FILE = os.path.join(DATA_DIR, "profile.json")
METRICS_FILE = os.path.join(DATA_DIR, "metrics.json")
APPLICATIONS_FILE = os.path.join(DATA_DIR, "applications.json")

class PersistenceManager:
    def __init__(self):
        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR)

    def save_data(self, profile: CandidateProfile, metrics: Dict[str, int], applications: List[Application]):
        """Saves current system state to JSON files."""
        # Save Profile
        if profile:
            with open(PROFILE_FILE, "w", encoding="utf-8") as f:
                f.write(profile.model_dump_json(indent=2))

        # Save Metrics
        with open(METRICS_FILE, "w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=2)

        # Save Applications
        # Application contains UUIDs and Datetimes, need robust serialization
        # Pydantic's model_dump_json works for individual models, but for a list we need to handle it.
        # Simplest way for pydantic v2:
        app_list_json = [app.model_dump(mode='json') for app in applications]
        with open(APPLICATIONS_FILE, "w", encoding="utf-8") as f:
            json.dump(app_list_json, f, indent=2, ensure_ascii=False)

    def load_data(self):
        """
        Loads system state. Returns tuple (profile, metrics, applications).
        Returns (None, None, None) if files don't exist.
        """
        profile = None
        metrics = None
        applications = []

        if os.path.exists(PROFILE_FILE):
            with open(PROFILE_FILE, "r", encoding="utf-8") as f:
                try:
                    profile = CandidateProfile.model_validate_json(f.read())
                except:
                    pass # Corrupt or old format

        if os.path.exists(METRICS_FILE):
            with open(METRICS_FILE, "r", encoding="utf-8") as f:
                metrics = json.load(f)

        if os.path.exists(APPLICATIONS_FILE):
            with open(APPLICATIONS_FILE, "r", encoding="utf-8") as f:
                try:
                    raw_apps = json.load(f)
                    applications = [Application.model_validate(app) for app in raw_apps]
                except:
                    pass

        return profile, metrics, applications
