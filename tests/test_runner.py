import unittest
import json
import os
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

# Ensure src is in path
sys.path.append(os.getcwd())

from src.core import runner

class TestReadQueue(unittest.TestCase):
    def setUp(self):
        self.temp_dir = TemporaryDirectory()
        self.queue_path = Path(self.temp_dir.name) / "queue.jsonl"
        # Patch runner.QUEUE_PATH
        self.original_queue_path = runner.QUEUE_PATH
        runner.QUEUE_PATH = self.queue_path

    def tearDown(self):
        runner.QUEUE_PATH = self.original_queue_path
        self.temp_dir.cleanup()

    def test_read_normal(self):
        data = [{"id": i} for i in range(10)]
        with open(self.queue_path, "w") as f:
            for item in data:
                f.write(json.dumps(item) + "\n")

        items = runner.read_queue(limit=5)
        self.assertEqual(len(items), 5)
        self.assertEqual(items[0]["id"], 0)
        self.assertEqual(items[4]["id"], 4)

    def test_read_limit_exceeds_file(self):
        data = [{"id": i} for i in range(3)]
        with open(self.queue_path, "w") as f:
            for item in data:
                f.write(json.dumps(item) + "\n")

        items = runner.read_queue(limit=10)
        self.assertEqual(len(items), 3)

    def test_empty_file(self):
        self.queue_path.touch()
        items = runner.read_queue(limit=10)
        self.assertEqual(items, [])

    def test_missing_file(self):
        if self.queue_path.exists():
            self.queue_path.unlink()
        items = runner.read_queue(limit=10)
        self.assertEqual(items, [])

    def test_malformed_json(self):
        with open(self.queue_path, "w") as f:
            f.write('{"id": 1}\n')
            f.write('GARBAGE\n')
            f.write('{"id": 3}\n')

        items = runner.read_queue(limit=10)
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]["id"], 1)
        self.assertEqual(items[1]["id"], 3)

if __name__ == "__main__":
    unittest.main()
