import pytest
import os
from pathlib import Path
from app import app, db

@pytest.fixture(autouse=True)
def setup_data_dir():
    """Ensure data directory exists for tests"""
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    yield
    # Cleanup after tests
    for file in data_dir.glob("*"):
        file.unlink()

@pytest.fixture(scope="session")
def docker_compose_file(pytestconfig):
    return str(pytestconfig.rootpath / "docker-compose.test.yml")

@pytest.fixture(scope="session")
def docker_ip(pytestconfig):
    return "localhost"

@pytest.fixture(scope="session")
def docker_port(pytestconfig):
    return 5001
