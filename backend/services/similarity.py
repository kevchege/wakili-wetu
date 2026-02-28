from sentence_transformers import SentenceTransformer, util

model = SentenceTransformer('all-MiniLM-L6-v2')

def find_similar(query, documents):
    query_embedding = model.encode(query)
    doc_embeddings = model.encode(documents)

    scores = util.cos_sim(query_embedding, doc_embeddings)

    return scores