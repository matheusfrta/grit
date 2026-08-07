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

## Installation

```bash
pip install grit-toolkit
```

## Quick Usage

### Retry
```python
from grit import retry, expo, decorr

@retry(tries=3, wait=expo(base=0.1, cap=5.0))
def fetch_user(user_id):
    return api.get(f"/users/{user_id}")
```

### Circuit Breaker
```python
from grit import breaker

db_breaker = breaker(fails=5, reset_after=30.0, name="postgres")

@db_breaker
def query_db():
    ...
```

### Timeout
```python
from grit import timeout

@timeout(2.5)
def heavy_computation():
    ...
```

### Rate Limiter
```python
from grit import limiter

lim = limiter(rate=10, per=1.0, burst=20)

@lim
def make_api_request():
    ...
```

### Bulkhead
```python
from grit import bulkhead

@bulkhead(size=5, timeout=1.0)
async def process_job():
    ...
```

### Fallback
```python
from grit import fallback

@fallback(value={"status": "offline"})
def get_live_feed():
    raise ConnectionError("Service unreachable")
```

### Composing Policies
```python
from grit import policy, fallback, timeout, retry, breaker, constant

api_policy = policy(
    fallback(value={"cached": True}),
    timeout(3.0),
    retry(tries=3, wait=constant(0.2)),
    breaker(fails=5, reset_after=15.0)
)

@api_policy
def get_data():
    ...
```

## Running Tests

```bash
pytest
```