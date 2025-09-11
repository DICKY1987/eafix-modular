import time, random


def with_retry(fn, attempts=2, backoff=(2, 5)):
    last = None
    for i in range(attempts):
        try:
            return fn()
        except Exception as e:
            last = e
            if i < attempts - 1:
                time.sleep(backoff[min(i, len(backoff) - 1)] + random.random())
    raise last

