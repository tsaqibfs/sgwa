"""Reject non-test databases before destructive test setup can connect."""
import re
from sqlalchemy.engine import make_url


def validated_test_url(value: str) -> str:
    try:
        url = make_url(value)
        valid = url.get_backend_name() == 'mysql' and re.fullmatch(r'sgwa_test[A-Za-z0-9_]*', url.database or '')
    except Exception:
        valid = False
    if not valid:
        raise ValueError('Use a dedicated MySQL sgwa_test database')
    return value
