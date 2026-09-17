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

EVAL_DIR = BASE_DIR / "app" / "eval"
GOLDEN_SET_PATH = EVAL_DIR / "golden_set.json"
EVAL_RESULT_PATH = EVAL_DIR / "eval_result.json"

# max embedding dimention
EMBED_DIM = 384
ENABLE_LARGE_ANSWER_STRATEGY = os.getenv("ENABLE_LARGE_ANSWER_STRATEGY", "False") == "True"

API_KEY=os.environ["GROQ_API_KEY"]