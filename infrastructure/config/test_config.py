def test_config_defaults():
    from infrastructure.config import load_config
    config = load_config()
    assert "watch_folders" in config
    assert "personality" in config
