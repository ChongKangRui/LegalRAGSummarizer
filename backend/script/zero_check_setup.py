import os

import numpy as np
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq(api_key=os.environ["GROQ_API_KEY"])


response = client.chat.completions.create(
     model="openai/gpt-oss-20b",
     messages=[{"role": "user", "content": "Say hello in one short sentence."}],
)
print(response.choices[0].message.content)

def cosine_similarity(a,b):
    return np.dot(a,b) / (np.linalg.norm(a) * np.linalg.norm(b))

