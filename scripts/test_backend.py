"""Load local test DB URL without exposing credentials in shell history."""
import os
from dotenv import dotenv_values
import pytest

url=dotenv_values('.env').get('TEST_DATABASE_URL')
if url:
    os.environ['TEST_DATABASE_URL']=url
raise SystemExit(pytest.main(['-q']))
