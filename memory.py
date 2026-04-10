import json
import os
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
