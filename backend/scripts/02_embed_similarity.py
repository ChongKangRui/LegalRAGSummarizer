from sentence_transformers import SentenceTransformer

momdel = SentenceTransformer("BAAI/bge-small-en-v1.5");
vector = model.encode("License shall pay the annual license fee within thirty days")