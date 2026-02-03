import time
import shutil
import tempfile
from pathlib import Path
from src.core.sources import enqueue, enqueue_urls
import src.core.sources as sources

def benchmark_enqueue(n=1000):
    # Setup temporary file
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        temp_path = Path(tmp.name)

    # Monkey patch QUEUE_PATH
    original_path = sources.QUEUE_PATH
    sources.QUEUE_PATH = temp_path

    try:
        # 1. Benchmark Single Enqueue
        start_time = time.time()
        for i in range(n):
            enqueue("benchmark", f"http://example.com/{i}")
        end_time = time.time()

        duration_single = end_time - start_time
        print(f"Single Enqueue {n} items took {duration_single:.4f} seconds")
        print(f"Average time per item: {duration_single/n:.6f} seconds")

        # Reset file
        temp_path.unlink()
        temp_path.touch()

        # 2. Benchmark Batch Enqueue
        urls = [f"http://example.com/{i}" for i in range(n)]

        start_time = time.time()
        enqueue_urls("benchmark", urls)
        end_time = time.time()

        duration_batch = end_time - start_time
        print(f"Batch Enqueue {n} items took {duration_batch:.4f} seconds")
        print(f"Average time per item: {duration_batch/n:.6f} seconds")

        # Calculate improvement
        if duration_batch > 0:
            speedup = duration_single / duration_batch
            print(f"Speedup: {speedup:.2f}x")

    finally:
        # Restore QUEUE_PATH and cleanup
        sources.QUEUE_PATH = original_path
        if temp_path.exists():
            temp_path.unlink()

if __name__ == "__main__":
    benchmark_enqueue()
