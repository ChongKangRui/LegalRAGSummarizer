
from groq import Groq
from functools import cache
from app.config import API_KEY


@cache
def get_groq_client() -> Groq:
    client = Groq(api_key=API_KEY)
    return client



