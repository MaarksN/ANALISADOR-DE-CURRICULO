from src.core.models import Application
from datetime import datetime, timedelta
import random

class FollowUpAgent:
    def __init__(self):
        pass

    def check_for_follow_up(self, applications: list[Application]) -> list[str]:
        """
        Checks applications that need a follow-up action.
        Returns a list of messages describing the actions taken.
        """
        actions = []
        for app in applications:
            # Simulate "Applied" applications that are older than X (simulated) seconds
            # In real life this would be days.
            # We don't have a real time delta in this simulation loop, so we'll use random chance
            # for demo purposes to simulate "time passing" or just trigger on a few.

            if app.status == "Aplicado" and random.random() < 0.1:
                # Simulate sending a follow-up email
                actions.append(f"Follow-up enviado para a vaga {app.job_id} na plataforma {app.platform}.")
                app.notes += " | Follow-up enviado."

        return actions
