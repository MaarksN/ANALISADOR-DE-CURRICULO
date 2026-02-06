import time
import os
import shutil
import tempfile
from unittest.mock import patch
from datetime import date

# Patch DATA_DIR before importing PersistenceManager if possible,
# but it is a module level constant.
# We will patch it using unittest.mock during execution.

from src.core.models import CandidateProfile, Application, Resume, Experience, Education, Skill
from src.core.persistence import PersistenceManager

def create_dummy_data():
    profile = CandidateProfile(
        name="John Doe",
        email="john@example.com",
        phone="1234567890",
        summary="Experienced Developer",
        experiences=[
            Experience(
                title="Senior Dev",
                company="Tech Corp",
                start_date=date(2020, 1, 1),
                description="Built things."
            )
        ],
        education=[
            Education(
                institution="University",
                degree="BS CS",
                start_date=date(2016, 1, 1),
                field_of_study="CS"
            )
        ],
        skills=[Skill(name="Python", level="Expert")]
    )

    applications = []
    # Create a decent amount of history to make serialization noticeable
    for i in range(500):
        app = Application(
            job_id=f"job_{i}",
            profile_id=profile.id,
            resume_id=profile.id, # reusing uuid for simplicity
            platform="LinkedIn"
        )
        applications.append(app)

    metrics = {"scanned": 1000, "applied": 500}

    return profile, metrics, applications

def benchmark_save_inside_loop(pm, profile, metrics, applications, iterations=10):
    start_time = time.perf_counter()

    for i in range(iterations):
        # Simulate adding a new application
        new_app = Application(
            job_id=f"new_job_{i}",
            profile_id=profile.id,
            resume_id=profile.id,
            platform="LinkedIn"
        )
        applications.append(new_app)
        metrics["applied"] += 1

        # The inefficient call
        pm.save_data(profile, metrics, applications)

    end_time = time.perf_counter()
    return end_time - start_time

def benchmark_save_outside_loop(pm, profile, metrics, applications, iterations=10):
    start_time = time.perf_counter()

    for i in range(iterations):
        # Simulate adding a new application
        new_app = Application(
            job_id=f"new_job_opt_{i}",
            profile_id=profile.id,
            resume_id=profile.id,
            platform="LinkedIn"
        )
        applications.append(new_app)
        metrics["applied"] += 1

    # The optimized call
    pm.save_data(profile, metrics, applications)

    end_time = time.perf_counter()
    return end_time - start_time

def run_benchmark():
    # Create a temp directory for data
    temp_dir = tempfile.mkdtemp()

    # Patch the constants in persistence module
    with patch("src.core.persistence.DATA_DIR", temp_dir), \
         patch("src.core.persistence.PROFILE_FILE", os.path.join(temp_dir, "profile.json")), \
         patch("src.core.persistence.METRICS_FILE", os.path.join(temp_dir, "metrics.json")), \
         patch("src.core.persistence.APPLICATIONS_FILE", os.path.join(temp_dir, "applications.json")):

        pm = PersistenceManager()

        # Prepare data
        profile, metrics, applications = create_dummy_data()

        # Benchmark inefficient
        # Copy list to not affect the next run
        apps_1 = list(applications)
        metrics_1 = metrics.copy()

        print("Running benchmark: Save INSIDE loop...")
        duration_inside = benchmark_save_inside_loop(pm, profile, metrics_1, apps_1, iterations=20)
        print(f"Time taken (Inside Loop): {duration_inside:.4f} seconds")

        # Benchmark optimized
        apps_2 = list(applications)
        metrics_2 = metrics.copy()

        print("Running benchmark: Save OUTSIDE loop...")
        duration_outside = benchmark_save_outside_loop(pm, profile, metrics_2, apps_2, iterations=20)
        print(f"Time taken (Outside Loop): {duration_outside:.4f} seconds")

        if duration_inside > 0:
            improvement = (duration_inside - duration_outside) / duration_inside * 100
            print(f"Improvement: {improvement:.2f}%")
            print(f"Speedup: {duration_inside / duration_outside:.2f}x")

    # Cleanup
    shutil.rmtree(temp_dir)

if __name__ == "__main__":
    run_benchmark()
