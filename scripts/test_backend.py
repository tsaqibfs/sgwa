"""Load local test DB URL without exposing credentials in shell history."""
import os
import sys
from pathlib import Path
from dotenv import dotenv_values
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from backend.tests.safety import validated_test_url

url=dotenv_values('.env').get('TEST_DATABASE_URL')
if url:
    os.environ['TEST_DATABASE_URL']=validated_test_url(url)
raise SystemExit(pytest.main(['-q']))
