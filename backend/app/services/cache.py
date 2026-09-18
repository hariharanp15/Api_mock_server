"""Best-effort Redis cache; API behaviour never depends on Redis availability."""
import json
import redis
from ..config import settings

try:
    client = redis.from_url(settings.redis_url, decode_responses=True, socket_connect_timeout=0.2, socket_timeout=0.2)
except Exception:
    client = None

def get_json(key: str):
    try:
        raw = client and client.get(key)
        return json.loads(raw) if raw else None
    except Exception:
        return None

def set_json(key: str, value, seconds: int = 30):
    try:
        if client: client.setex(key, seconds, json.dumps(value, default=str))
    except Exception:
        pass

def invalidate(key: str):
    try:
        if client: client.delete(key)
    except Exception:
        pass
