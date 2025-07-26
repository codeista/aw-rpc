"""
Pytest configuration for UI tests

Ensures proper cleanup of Selenium browser instances
"""

import pytest
from selenium import webdriver
import atexit
import signal
import sys
import psutil
import os

# Track all active drivers
active_drivers = []

def cleanup_all_drivers():
    """Force cleanup of all WebDriver instances"""
    print("\n🧹 Cleaning up browser instances...")
    
    # Close all tracked drivers
    for driver in active_drivers:
        try:
            driver.quit()
        except:
            pass
    active_drivers.clear()
    
    # Kill any remaining Chrome processes
    try:
        for proc in psutil.process_iter(['pid', 'name']):
            if 'chrome' in proc.info['name'].lower() or 'chromedriver' in proc.info['name'].lower():
                try:
                    proc.kill()
                except:
                    pass
    except:
        pass

# Register cleanup handlers
atexit.register(cleanup_all_drivers)

def signal_handler(sig, frame):
    """Handle interruption signals"""
    cleanup_all_drivers()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

@pytest.fixture(autouse=True)
def cleanup_fixture(request):
    """Ensure cleanup after each test"""
    yield
    # This runs after each test
    cleanup_all_drivers()

@pytest.fixture
def driver(request):
    """Provide a WebDriver instance with automatic cleanup"""
    from selenium.webdriver.chrome.options import Options
    
    chrome_options = Options()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--headless')  # Run in headless mode to avoid window spam
    
    driver = webdriver.Chrome(options=chrome_options)
    active_drivers.append(driver)
    
    def cleanup():
        """Cleanup function for this specific driver"""
        try:
            driver.quit()
            if driver in active_drivers:
                active_drivers.remove(driver)
        except:
            pass
    
    request.addfinalizer(cleanup)
    return driver

def pytest_configure(config):
    """Configure pytest"""
    # Set up markers
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "ui: marks tests as UI tests"
    )

def pytest_sessionfinish(session, exitstatus):
    """Clean up at the end of the test session"""
    cleanup_all_drivers()

def pytest_exception_interact(node, call, report):
    """Handle test exceptions"""
    if report.failed:
        # Ensure cleanup on test failure
        cleanup_all_drivers()