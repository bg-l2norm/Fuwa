import json
import os
import math
import re
from collections import Counter
from pathlib import Path

MEMORY_FILE = "memory.json"

_cached_memory = None

def load_memory() -> dict:
    global _cached_memory
    if _cached_memory is not None:
        return _cached_memory

    if not os.path.exists(MEMORY_FILE):
        _cached_memory = {}
        return _cached_memory

    try:
        with open(MEMORY_FILE, "r") as f:
            _cached_memory = json.load(f)
            return _cached_memory
    except Exception as e:
        print(f"Error loading memory: {e}")
        _cached_memory = {}
        return _cached_memory

def save_memory(memory_data: dict):
    global _cached_memory
    try:
        with open(MEMORY_FILE, "w") as f:
            json.dump(memory_data, f, indent=4)
        _cached_memory = memory_data
    except Exception as e:
        print(f"Error saving memory: {e}")

def update_memory(filename: str, summary: str):
    memory_data = load_memory()
    memory_data[filename] = summary
    save_memory(memory_data)


def update_memories(updates: dict):
    memory_data = load_memory()
    memory_data.update(updates)
    save_memory(memory_data)


def get_memory(filename: str) -> str:
    memory_data = load_memory()
    return memory_data.get(filename, "")

def get_all_memories() -> str:
    memory_data = load_memory()
    if not memory_data:
        return "No file memories yet."

    parts = []
    for filename, summary in memory_data.items():
        parts.append(f"File: {filename}\nSummary: {summary}\n")
    return "\n".join(parts)

def _tokenize(text: str) -> list[str]:
    return re.findall(r'\w+', text.lower())

def search_memory(query: str, top_k: int = 3) -> str:
    """Uses a pure Python TF-IDF approach to find most relevant file summaries."""
    memory_data = load_memory()
    if not memory_data:
        return "No file memories yet."

    docs = list(memory_data.values())
    filenames = list(memory_data.keys())

    query_tokens = _tokenize(query)
    if not query_tokens:
        # Fallback if no query tokens
        parts = []
        for filename, summary in list(memory_data.items())[-top_k:]:
            parts.append(f"File: {filename}\nSummary: {summary}\n")
        return "\n".join(parts)

    doc_tokens_list = [_tokenize(filenames[i] + " " + docs[i]) for i in range(len(docs))]

    # Compute IDF
    num_docs = len(docs)
    df = Counter()
    for doc_tokens in doc_tokens_list:
        df.update(set(doc_tokens))

    idf = {}
    for token, count in df.items():
        idf[token] = math.log((num_docs + 1) / (count + 1)) + 1

    # Compute query vector
    query_tf = Counter(query_tokens)
    query_vec = {token: count * idf.get(token, 1.0) for token, count in query_tf.items()}
    query_norm = math.sqrt(sum(v * v for v in query_vec.values()))
    if query_norm == 0:
        query_norm = 1.0

    # Compute doc scores (cosine similarity)
    scores = []
    for i, doc_tokens in enumerate(doc_tokens_list):
        doc_tf = Counter(doc_tokens)
        doc_vec = {token: count * idf.get(token, 1.0) for token, count in doc_tf.items() if token in query_vec}
        doc_norm = math.sqrt(sum((count * idf.get(token, 1.0)) ** 2 for token, count in doc_tf.items()))
        if doc_norm == 0:
            doc_norm = 1.0

        dot_product = sum(query_vec[token] * doc_vec.get(token, 0) for token in query_vec)
        cosine_sim = dot_product / (query_norm * doc_norm)
        scores.append((cosine_sim, i))

    scores.sort(reverse=True, key=lambda x: x[0])

    parts = []
    for score, i in scores[:top_k]:
        filename = filenames[i]
        summary = docs[i]
        parts.append(f"File: {filename}\nSummary: {summary}\n")

    return "\n".join(parts)
