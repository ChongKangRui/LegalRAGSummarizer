# from sentence_transformers import SentenceTransformer
from functools import cache

from fastembed import TextEmbedding
import numpy as np


@cache
def get_embedder():
    return TextEmbedding(model_name="BAAI/bge-small-en-v1.5") 
   # return SentenceTransformer("all-MiniLM-L6-v2")