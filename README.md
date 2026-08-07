# Grit

A lightweight, zero-dependency resilience toolkit for Python applications (sync and async).

In distributed systems, external dependencies like databases, microservices, and HTTP APIs will fail. **Grit** provides failure-handling primitives to keep your application stable during outages, network spikes, and service degradation.

## What it's for

Grit helps you write fault-tolerant Python applications by addressing common distributed systems problems:

- **Transient Errors**: Network blips or temporary HTTP 503s that recover after a quick retry.
- **Cascading Failures**: An offline database blocking worker threads and taking down the whole system.
- **Resource Exhaustion**: Too many concurrent incoming requests crashing memory or CPU.
- **Upstream Rate Limits**: Exceeding rate limits on external APIs (e.g., Stripe, OpenAI).
- **Service Degradation**: Knowing when to fail fast or return stale cached data instead of timing out.

## Key Features

- **Sync & Async Native**: Every primitive works seamlessly on sync functions, standard threads, and `asyncio` coroutines.
- **Zero External Dependencies**: Implemented using standard library modules (`asyncio`, `threading`, `time`, `signal`).
- **Composable**: Combine multiple resilience patterns into a single policy decorator.
- **Flexible Backoffs**: Includes constant, linear, exponential, fibonacci, full jitter, and decorrelated jitter backoff algorithms.

## Common Use Cases

### 1. Flaky HTTP APIs (Retry + Backoff + Timeout)
Retry unstable third-party HTTP calls with exponential backoff and jitter to prevent hammering the server, capped by a strict execution timeout.

### 2. Microservice & Database Outages (Circuit Breaker)
Stop sending requests to a failing service immediately once a threshold is reached. Allows the downstream dependency to recover instead of choking it with retry traffic.

### 3. API Client Throttling (Rate Limiter)
Respect third-party rate limits using a token bucket rate limiter to smooth out request spikes.

### 4. Protecting Shared Resources (Bulkhead)
Isolate resource consumption. Limit max concurrent calls to expensive operations (e.g., image processing, heavy DB queries) so they don't starve other parts of your app.

### 5. Fallbacks & Graceful Degradation (Fallback)
Return fallback values or cached data when downstream calls fail, giving users a degraded experience instead of an unhandled error.

---

## Installation

```bash
pip install pygrit
```

## Usage Examples

### Retry
Automatically retries failing functions. Works with custom backoff strategies.

```python
from grit import retry, expo, decorr

@retry(tries=3, wait=expo(base=0.1, cap=5.0))
def fetch_user(user_id):
    # Retries up to 3 times with exponential backoff
    return api.get(f"/users/{user_id}")

# Async coroutines work natively
@retry(tries=5, wait=decorr(base=0.2, cap=10.0))
async def fetch_user_async(user_id):
    return await async_api.get(f"/users/{user_id}")
```

### Circuit Breaker
Monitors failures and "opens" the circuit when failures exceed a limit, raising `BreakerOpen` on subsequent calls until `reset_after` seconds pass.

```python
from grit import breaker

db_breaker = breaker(fails=5, reset_after=30.0, name="postgres")

@db_breaker.on_change
def log_state(name, state):
    print(f"Breaker '{name}' state changed to {state}")

@db_breaker
def query_db():
    ...

# Context manager usage is also supported
with db_breaker:
    db.execute(...)
```

### Timeout
Enforces execution time limits. Uses `signal.ITIMER_REAL` on the main thread for fast sync timeouts, daemon threads as a fallback, and `asyncio.wait_for` for coroutines.

```python
from grit import timeout

@timeout(2.5)
def heavy_computation():
    ...
```

### Rate Limiter
Token bucket implementation for rate limiting operations.

```python
from grit import limiter

# Allow 10 requests per second, with burst capacity up to 20
lim = limiter(rate=10, per=1.0, burst=20)

@lim
def make_api_request():
    ...
```

### Bulkhead
Limits execution concurrency to protect system capacity. Excess requests raise `BulkheadFull`.

```python
from grit import bulkhead

# Allow at most 5 concurrent calls
@bulkhead(size=5, timeout=1.0)
async def process_job():
    ...
```

### Fallback
Catches specified exceptions and returns a default static value or executes a rescue function.

```python
from grit import fallback

@fallback(value={"status": "offline", "data": []})
def get_live_feed():
    raise ConnectionError("Service unreachable")

# Dynamic fallback function
@fallback(fn=lambda err: f"Handled error: {err}")
def calculate():
    ...
```

### Composing Policies
Chain multiple primitives together. Layers execution from outer to inner.

```python
from grit import policy, fallback, timeout, retry, breaker, constant

# Order: Fallback (outermost) -> Timeout -> Retry -> Breaker (innermost)
api_policy = policy(
    fallback(value={"cached": True, "items": []}),
    timeout(3.0),
    retry(tries=3, wait=constant(0.2)),
    breaker(fails=5, reset_after=15.0, name="external-api")
)

@api_policy
def get_dashboard_data():
    return external_service.fetch()
```

---

## Backoff Algorithms

Available in `grit.backoff`:

- `constant(base=1.0)`: Fixed wait time.
- `linear(base=1.0)`: Linearly increasing wait time (`base * attempt`).
- `expo(base=1.0, factor=2.0, cap=60.0)`: Exponential growth.
- `fibo(base=1.0, cap=60.0)`: Fibonacci sequence growth.
- `jitter(backoff_fn, spread=1.0)`: Adds random spread to another backoff.
- `decorr(base=1.0, cap=60.0)`: Decorrelated jitter strategy.

## Exception Hierarchy

All exceptions inherit from `GritError`:

- `GritError`
  - `RetryExhausted` (attributes: `attempts`, `last`)
  - `BreakerOpen` (attributes: `name`, `retry_after`)
  - `TimeoutExceeded` (attributes: `seconds`)
  - `BulkheadFull` (attributes: `size`)
  - `LimitExceeded` (attributes: `timeout`)

## Running Tests

```bash
pytest
```