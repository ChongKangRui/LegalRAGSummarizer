
from rank_bm25 import BM25Okapi
import json
from app.config import VECTORS_META
from functools import cache


import numpy as np
import re

import threading
_lock = threading.Lock()

def _tokenize(text : str)->list[str]:
    """
    a very good lesson, lower it isn't enough cause bm_25 unable to detect
    'seperation' and 'seperation.' is different. 
    'date' and 'date)' are different as well
    Thus, tokenization should only contain number + character
    """
    #return text.lower().split()
    return re.findall(r"[a-z0-9]+", text.lower())

@cache
def _load():
    with _lock:
        with open(VECTORS_META, encoding="utf-8") as f:
            meta = json.load(f)
    
        tokenized_corpus = [_tokenize(m["text"]) for m in meta]
        bm25 = BM25Okapi(tokenized_corpus)
        
        return bm25, meta
    


def query(query_text: str,top_k: int = 10, where: dict | None = None):
    bm25, meta = _load()

    scores = bm25.get_scores(_tokenize(query_text))

    if where:
            # np.fromiter build a numpy array without create an intermediate python list
            mask = np.fromiter((all(m["metadata"].get(k) == v for k,v in 
            where.items()) for m in meta), 
            dtype=bool,
            count=len(meta))

            scores = np.where(mask, scores, -np.inf)
   
    idx = np.argsort(scores)[::-1][:top_k]
    
    return [
        {**meta[i], "score": float(scores[i])}
        for i in idx
        if np.isfinite(scores[i])
    ]


if __name__ == "__main__":
    _load()
    q = query("How can i get refund from foodpanda", 3, where={"doc_id" : "tos-foodpanda"})
    print(q)