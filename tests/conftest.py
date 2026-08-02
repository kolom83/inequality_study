import os
import sys
from pathlib import Path

import pytest
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
load_dotenv(PROJECT_ROOT / ".env")


@pytest.fixture(autouse=True)
def ensure_wid_api_key():
    if not os.getenv("WID_API_KEY"):
        os.environ["WID_API_KEY"] = "test-key"
    yield
