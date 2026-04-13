"""Shared pytest configuration and custom markers."""


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "llm: test requires Ollama to be running (skipped in CI)",
    )
