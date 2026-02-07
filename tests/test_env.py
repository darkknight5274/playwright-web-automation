import playwright
import pytest
import yaml
import structlog
from utils.logger import logger
from utils.session import SessionManager

def test_imports():
    assert playwright is not None
    assert yaml is not None
    assert structlog is not None
    assert logger is not None
    assert SessionManager is not None

def test_logger():
    logger.info("Testing logger", status="ok")

@pytest.mark.skip(reason="Requires browsers to be installed, which might take too long in this environment")
def test_playwright_session():
    session = SessionManager()
    page = session.start(headless=True)
    assert page is not None
    session.stop()
