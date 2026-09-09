from pathlib import Path
from dotenv import load_dotenv
import os
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent   # -> backend/
DOCUMENTS_DIR = BASE_DIR / "documents"
DATA_DIR = BASE_DIR / "data"

VECTOR_BACKEND = os.getenv("VECTOR_BACKEND", "chroma")   # "chroma" | "numpy"
VECTORS_PATH   = DATA_DIR / "vectors.npy"
VECTORS_META   = DATA_DIR / "vectors.meta.json"

EMBED_DIM = 384

API_KEY=os.environ["GROQ_API_KEY"]