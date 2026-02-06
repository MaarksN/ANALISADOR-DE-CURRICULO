import sys
import os
import time
import sqlite3
from pathlib import Path
from datetime import date
import importlib

# Ensure we can import src
sys.path.append(os.getcwd())

# Define Test DB
TEST_DB = Path("test_perf.db")

# 1. Import db module and patch DB_PATH
import src.core.db as db
db.DB_PATH = TEST_DB

# 2. Import runner (it should pick up the patched DB_PATH if we are lucky,
#    but since 'from' imports bind objects, we might need to be careful if runner was already imported)
#    Since this is a fresh script, it should be fine.
import src.core.runner as runner

# Double check patching
if runner.DB_PATH != TEST_DB:
    print(f"Warning: runner.DB_PATH ({runner.DB_PATH}) != TEST_DB. Patching directly.")
    runner.DB_PATH = TEST_DB

from src.core.db import init_db, upsert_job

def setup():
    if TEST_DB.exists():
        os.remove(TEST_DB)
    # Initialize DB
    init_db()

    # Insert some data
    # We need to insert directly or via upsert_job.
    # upsert_job opens its own connection to DB_PATH (which we patched in db module)

    # Insert 50 'applied' jobs for today
    for i in range(50):
        upsert_job("linkedin", f"https://linkedin.com/jobs/view/{i}", "applied",
                   title=f"Job {i}", company="Comp", location="Loc")

    # Insert some non-applied
    for i in range(50, 100):
        upsert_job("linkedin", f"https://linkedin.com/jobs/view/{i}", "seen",
                   title=f"Job {i}", company="Comp", location="Loc")

def cleanup():
    if TEST_DB.exists():
        try:
            os.remove(TEST_DB)
        except:
            pass

def benchmark_baseline(n=100):
    start = time.time()
    for _ in range(n):
        runner.count_applied_today()
    end = time.time()
    return end - start

def benchmark_optimized(n=100):
    # This will fail until we implement the optimization
    # We will wrap it in try/except or check signature

    # Open a connection
    conn = sqlite3.connect(TEST_DB)
    try:
        start = time.time()
        for _ in range(n):
            # Check if count_applied_today accepts 'con'
            try:
                runner.count_applied_today(con=conn)
            except TypeError:
                # Fallback to baseline if not implemented yet
                runner.count_applied_today()
        end = time.time()
        return end - start
    finally:
        conn.close()

if __name__ == "__main__":
    setup()
    try:
        print(f"Running benchmark with {TEST_DB}...")

        # Verify count is correct
        count = runner.count_applied_today()
        print(f"Count applied today: {count} (Expected 50)")

        # Warmup
        benchmark_baseline(10)

        # Measure Baseline
        n = 200
        duration = benchmark_baseline(n)
        print(f"Baseline ({n} calls): {duration:.4f}s")
        print(f"Avg per call: {duration/n*1000:.2f}ms")

        # Measure Optimized
        duration_opt = benchmark_optimized(n)
        print(f"Optimized ({n} calls): {duration_opt:.4f}s")
        print(f"Avg per call: {duration_opt/n*1000:.2f}ms")

        improvement = (duration - duration_opt) / duration * 100
        print(f"Improvement: {improvement:.2f}%")

    finally:
        cleanup()
