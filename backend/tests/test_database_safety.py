import importlib.util
import pytest


def test_application_url_is_rejected_before_any_connection():
    assert importlib.util.find_spec('backend.tests.safety'), 'Central database safety guard missing'
    from backend.tests.safety import validated_test_url
    for url in ['mysql+pymysql://user:password@localhost/sgwa_demo','mysql+pymysql://user:password@localhost/mysql','sqlite:///sgwa_test.db','mysql+pymysql://localhost/sgwa_test%2Fproduction']:
        with pytest.raises(ValueError):
            validated_test_url(url)
    safe='mysql+pymysql://user:password@localhost/sgwa_test_codex'
    assert validated_test_url(safe)==safe
