"""
Configuration constants for local.ch scraper
"""

import os

# Base directory (project root)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Browser configuration
FIREFOX_PATH = r"C:\Program Files\Firefox Developer Edition\firefox.exe"
GECKODRIVER_PATH = r"C:\Users\aapra\.wdm\drivers\geckodriver\win64\v0.36.0\geckodriver.exe"

# File paths (relative to project root)
PROXY_FILE = os.path.join(BASE_DIR, "proxies", "proxylist.txt")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
DATA_DIR = os.path.join(BASE_DIR, "data")

# Browser settings
HEADLESS = True
PAGE_LOAD_TIMEOUT = 30
ELEMENT_WAIT_TIMEOUT = 10

# Default scraping parameters (can be overridden via CLI)
DEFAULT_PAGES = 150
DEFAULT_WORKERS = 1  # Safe default, user can increase (1-20)
DEFAULT_WORKERS_NO_PROXY = 1
DEFAULT_MAX_ERRORS = 3
DEFAULT_DELAY = 0.3
DEFAULT_PROXY_COOLDOWN = 300  # 5 minutes

# Business name suffixes for classification
BUSINESS_SUFFIXES = [
    r'\bSA\b',
    r'\bSagl\b',
    r'\bSAGL\b',
    r'\bAG\b',
    r'\bGmbH\b',
    r'\bSrl\b',
    r'\bS\.r\.l\.\b',
    r'\b& Co\b',
    r'\bSnc\b',
    r'\bSNC\b',
]


def has_proxy_file():
    """Check if proxy file exists."""
    return os.path.exists(PROXY_FILE)


def ensure_output_dir():
    """Ensure output directory exists."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def ensure_data_dir():
    """Ensure data directory exists."""
    os.makedirs(DATA_DIR, exist_ok=True)


def get_db_path(db_name):
    """Get full path to database file."""
    ensure_data_dir()
    return os.path.join(DATA_DIR, db_name)
