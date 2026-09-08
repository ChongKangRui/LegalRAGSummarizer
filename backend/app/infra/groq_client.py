import os

from dotenv import load_dotenv
from groq import Groq
from functools import cache

load_dotenv()

@cache
def get_groq_client() -> Groq:
    client = Groq(api_key=os.environ["GROQ_API_KEY"])
    return client



