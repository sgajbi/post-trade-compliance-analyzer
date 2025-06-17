# backend/test/unit/test_settings.py
import os
import pytest
from pydantic import ValidationError
from core.config import Settings

# Helper function to clear relevant environment variables for tests
def _clear_settings_env_vars(monkeypatch):
    monkeypatch.delenv("CHROMA_DB_PATH", raising=False)
    monkeypatch.delenv("CHROMA_COLLECTION_NAME", raising=False)
    monkeypatch.delenv("EMBEDDING_MODEL_NAME", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("APP_NAME", raising=False) # Clear APP_NAME if it's set in env
    monkeypatch.delenv("ENV", raising=False) # Clear ENV if it's set in env

# --- Test Case 1: Test default settings loading (expecting ValidationError for missing required fields) ---
def test_default_settings_loading(monkeypatch, tmp_path):
    """
    Tests that a ValidationError is raised when required settings (like OPENAI_API_KEY) are not set
    and no .env file is present.
    """
    _clear_settings_env_vars(monkeypatch)
    # Change current working directory to a temporary path to ensure no real .env file is found
    monkeypatch.chdir(tmp_path)

    with pytest.raises(ValidationError) as excinfo:
        Settings()
    assert "OPENAI_API_KEY" in str(excinfo.value) # Check that the error message relates to OPENAI_API_KEY


# --- Test Case 2: Test settings loading from environment variables ---
def test_env_var_settings_loading(monkeypatch):
    """
    Tests that settings are loaded correctly from environment variables.
    """
    _clear_settings_env_vars(monkeypatch) # Clear existing env vars first
    monkeypatch.setenv("CHROMA_DB_PATH", "/tmp/my_test_db")
    monkeypatch.setenv("CHROMA_COLLECTION_NAME", "test_collection")
    monkeypatch.setenv("OPENAI_API_KEY", "test_openai_key_123")
    monkeypatch.setenv("APP_NAME", "Test App From Env")
    monkeypatch.setenv("ENV", "test") # Set ENV for consistent behavior

    settings = Settings()
    assert settings.APP_NAME == "Test App From Env"
    assert settings.CHROMA_DB_PATH == "/tmp/my_test_db"
    assert settings.CHROMA_COLLECTION_NAME == "test_collection"
    assert settings.OPENAI_API_KEY == "test_openai_key_123"
    assert settings.ENV == "test"

# --- Test Case 3: Test .env file loading (requires creating a temp .env) ---
def test_dot_env_file_settings_loading(tmp_path, monkeypatch):
    """
    Tests that settings are loaded correctly from a .env file.
    Uses pytest's tmp_path fixture to create a temporary .env file.
    """
    _clear_settings_env_vars(monkeypatch) # Clear existing env vars first

    # Create a temporary .env file in the tmp_path
    env_content = """
CHROMA_DB_PATH=/path/from/env_file
CHROMA_COLLECTION_NAME=env_collection
OPENAI_API_KEY=env_openai_key_from_file
APP_NAME=Test App From DotEnv
ENV=development
    """
    env_file = tmp_path / ".env"
    env_file.write_text(env_content)

    # Change current working directory to where the .env file is for Settings to find it
    monkeypatch.chdir(tmp_path)

    # Re-instantiate settings to pick up the new .env file
    settings = Settings()
    assert settings.APP_NAME == "Test App From DotEnv"
    assert settings.CHROMA_DB_PATH == "/path/from/env_file"
    assert settings.CHROMA_COLLECTION_NAME == "env_collection"
    assert settings.OPENAI_API_KEY == "env_openai_key_from_file"
    assert settings.ENV == "development"


# --- Test Case 4: Test required OpenAI API Key (explicitly checking for ValidationError) ---
def test_openai_api_key_missing_raises_error(monkeypatch, tmp_path):
    """
    Tests that a ValidationError is raised if OPENAI_API_KEY is not set.
    """
    _clear_settings_env_vars(monkeypatch) # Clear all env vars, including OPENAI_API_KEY
    # Change current working directory to a temporary path to ensure no real .env file is found
    monkeypatch.chdir(tmp_path)

    with pytest.raises(ValidationError) as excinfo:
        Settings()
    # Check that the error message relates to OPENAI_API_KEY
    assert "OPENAI_API_KEY" in str(excinfo.value)