import unittest
import shutil
import sqlite3
from pathlib import Path
from src.core import db

TEST_DB = Path("data") / "functional_test.db"

class TestDBFunctional(unittest.TestCase):
    def setUp(self):
        # Point db module to test db
        self.original_db_path = db.DB_PATH
        db.DB_PATH = TEST_DB

        if TEST_DB.exists():
            TEST_DB.unlink()

        # Initialize DB for test
        db.init_db()

    def tearDown(self):
        if TEST_DB.exists():
            TEST_DB.unlink()
        db.DB_PATH = self.original_db_path

    def test_upsert_and_seen(self):
        # 1. Insert new job
        db.upsert_job(
            platform="linkedin",
            job_url="http://linkedin.com/job/1",
            status="applied",
            title="Software Engineer",
            score=100
        )

        # 2. Verify with seen
        status = db.seen("linkedin", "http://linkedin.com/job/1")
        self.assertEqual(status, "applied")

        # 3. Update job
        db.upsert_job(
            platform="linkedin",
            job_url="http://linkedin.com/job/1",
            status="rejected",
            title="Software Engineer",
            score=100
        )

        # 4. Verify update
        status = db.seen("linkedin", "http://linkedin.com/job/1")
        self.assertEqual(status, "rejected")

if __name__ == "__main__":
    unittest.main()
