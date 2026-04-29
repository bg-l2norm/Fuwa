import pytest
from infrastructure.memory import search_memory

def test_search_memory_empty_query(monkeypatch):
    # Mock load_memory to return some sample data
    mock_data = {
        "file1.py": "Summary of file 1",
        "file2.py": "Summary of file 2",
        "file3.py": "Summary of file 3",
        "file4.py": "Summary of file 4"
    }
    monkeypatch.setattr("infrastructure.memory.load_memory", lambda: mock_data)

    # Call search_memory with an empty query
    # Default top_k is 3. Fallback logic returns last top_k items.
    result = search_memory("", top_k=3)

    # Verify the results are the last 3 items in the mock data
    assert "File: file2.py" in result
    assert "File: file3.py" in result
    assert "File: file4.py" in result
    assert "File: file1.py" not in result

def test_search_memory_no_tokens_query(monkeypatch):
    # Mock load_memory to return some sample data
    mock_data = {
        "file1.py": "Summary of file 1",
        "file2.py": "Summary of file 2"
    }
    monkeypatch.setattr("infrastructure.memory.load_memory", lambda: mock_data)

    # Call search_memory with a query that has no tokens (only punctuation/whitespace)
    result = search_memory("   !!!   ", top_k=2)

    # Verify fallback logic is triggered
    assert "File: file1.py" in result
    assert "File: file2.py" in result

def test_search_memory_empty_memory(monkeypatch):
    # Mock load_memory to return empty dict
    monkeypatch.setattr("infrastructure.memory.load_memory", lambda: {})

    # Call search_memory
    result = search_memory("some query")

    # Verify empty memory message
    assert result == "No file memories yet."
