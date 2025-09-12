from __future__ import annotations

from collections import deque

QUEUE = deque(maxlen=1000)  # bounded queue
CB_BACKOFF = (1, 2, 5)      # seconds
