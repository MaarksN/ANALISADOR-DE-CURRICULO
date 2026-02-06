import unittest
import shutil
import sqlite3
from pathlib import Path
from src.core import db

TEST_DB = Path("data") / "functional_test.db"

class TestDBFunctional(unittest.TestCase):
    def setUp(self):
        # Point db module to test db
        db.DB_PATH = TEST_DB
        # Clear any existing local connection in the thread
        if hasattr(db._local, "connection"):
            try:
                db._local.connection.close()
            except:
                pass
            del db._local.connection

        if TEST_DB.exists():
            TEST_DB.unlink()

    def tearDown(self):
        if hasattr(db._local, "connection"):
            db._local.connection.close()
            del db._local.connection
        if TEST_DB.exists():
            TEST_DB.unlink()

    def test_upsert_and_seen(self):
        db.init_db()

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

    def test_connection_persistence(self):
        # Verify that multiple calls use the same connection object
        db.init_db()
        con1 = db.get_connection()
        db.upsert_job("p", "u", "s")
        con2 = db.get_connection()

        self.assertIs(con1, con2)

        # Verify it works across "transactions"
        db.upsert_job("p2", "u2", "s")
        status = db.seen("p2", "u2")
        self.assertEqual(status, "s")

if __name__ == "__main__":
    unittest.main()
