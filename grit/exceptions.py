class GritError(Exception):
    pass


class RetryExhausted(GritError):
    def __init__(self, attempts, last):
        self.attempts = attempts
        self.last = last
        super().__init__(f"gave up after {attempts} attempt(s): {last}")


class BreakerOpen(GritError):
    def __init__(self, name, retry_after):
        self.name = name
        self.retry_after = retry_after
        label = name or "breaker"
        super().__init__(f"{label} is open, retry in {retry_after:.2f}s")


class TimeoutExceeded(GritError):
    def __init__(self, seconds):
        self.seconds = seconds
        super().__init__(f"timed out after {seconds}s")


class BulkheadFull(GritError):
    def __init__(self, size):
        self.size = size
        super().__init__(f"all {size} slot(s) busy")


class LimitExceeded(GritError):
    def __init__(self, timeout):
        self.timeout = timeout
        super().__init__(f"no token within {timeout}s")