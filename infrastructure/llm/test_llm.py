def test_generate_comment_error_path(monkeypatch):
    from infrastructure.llm import generate_comment

    # Mock simple_completion to raise an exception
    monkeypatch.setattr('infrastructure.llm.simple_completion', lambda **kwargs: exec('raise Exception("Test error")'))

    # Call generate_comment with dummy arguments
    result = generate_comment("test observation", "test personality", ["NORMAL"], "openai", "gpt-4", "test_key", "test memory")

    # Assert that the error is handled and returns the expected fallback message
    assert result == "(Axolotl looks confused...) Error: Test error"
