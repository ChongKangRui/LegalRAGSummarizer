
from groq import AsyncGroq, Groq
from functools import cache
from app.config import API_KEY

import threading
_lock = threading.Lock()

@cache
def get_groq_client() -> Groq:
    with _lock:
        client = Groq(api_key=API_KEY)
        return client


@cache
def get_async_groq_client()->AsyncGroq:
    with _lock:
        client = AsyncGroq(api_key=API_KEY)
        return client
