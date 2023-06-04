import time
import json

class TokenBucket:
    def __init__(self, rate, capacity):
        self._rate = rate
        self._capacity = capacity
        self._tokens = capacity
        self._last = time.time()

    def consume(self):
        if self._tokens < 1:
            return False
        self._tokens -= 1
        return True

    def refill(self):
        now = time.time()
        elapsed = now - self._last
        self._last_time = now
        self._tokens = min(self._capacity, self._tokens + elapsed * self._rate)

