from __future__ import annotations

import os
import time
from contextlib import contextmanager
from pathlib import Path


LOCK_DIR = Path(".ai/lock")


@contextmanager
def file_lock(timeout: float = 10.0, poll: float = 0.1):
    LOCK_DIR.parent.mkdir(parents=True, exist_ok=True)
    start = time.time()
    while True:
        try:
            os.mkdir(LOCK_DIR)
            break
        except FileExistsError:
            if time.time() - start > timeout:
                raise TimeoutError("Could not acquire lock")
            time.sleep(poll)
    try:
        yield
    finally:
        try:
            os.rmdir(LOCK_DIR)
        except FileNotFoundError:
            pass

