"""
Core scraping functions for local.ch
"""

import re
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from config import (
    FIREFOX_PATH, GECKODRIVER_PATH, HEADLESS,
    PAGE_LOAD_TIMEOUT, ELEMENT_WAIT_TIMEOUT
)


def get_driver(proxy=None):
    """
    Initialize Firefox WebDriver.

    Args:
        proxy: Optional proxy string "host:port"

    Returns:
        WebDriver instance
    """
    options = Options()
    options.binary_location = FIREFOX_PATH

    if HEADLESS:
        options.add_argument("--headless")

    # Configure proxy if provided
    if proxy:
        proxy_host, proxy_port = proxy.split(":")
        options.set_preference("network.proxy.type", 1)
        options.set_preference("network.proxy.http", proxy_host)
        options.set_preference("network.proxy.http_port", int(proxy_port))
        options.set_preference("network.proxy.ssl", proxy_host)
        options.set_preference("network.proxy.ssl_port", int(proxy_port))
        options.set_preference("network.proxy.no_proxies_on", "")

    # Timeout settings
    options.set_preference("dom.max_script_run_time", 30)
    options.set_preference("network.http.connection-timeout", 30)

    service = Service(GECKODRIVER_PATH)
    driver = webdriver.Firefox(service=service, options=options)
    driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)

    return driver


def safe_extract(driver, selector, attribute=None):
    """
    Safely extract text or attribute from an element.

    Args:
        driver: WebDriver instance
        selector: CSS selector
        attribute: Optional attribute to extract (default: text)

    Returns:
        Extracted value or None
    """
    try:
        element = driver.find_element(By.CSS_SELECTOR, selector)
        if attribute:
            return element.get_attribute(attribute)
        return element.text.strip()
    except:
        return None


def extract_links_from_page(driver, url):
    """
    Extract business links from a single search results page.

    Args:
        driver: WebDriver instance
        url: Search results page URL

    Returns:
        List of business page URLs
    """
    driver.get(url)

    wait = WebDriverWait(driver, ELEMENT_WAIT_TIMEOUT)
    try:
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.lR")))
    except:
        pass

    time.sleep(1)

    links = []
    try:
        result_divs = driver.find_elements(By.CSS_SELECTOR, "div.lR")
        for div in result_divs:
            try:
                link = div.find_element(By.TAG_NAME, "a")
                href = link.get_attribute("href")
                if href and "/d/" in href:
                    links.append(href)
            except:
                continue
    except:
        pass

    return links


def extract_links_paginated(driver, base_url, num_pages, delay=0.5):
    """
    Extract links from multiple search result pages.

    Args:
        driver: WebDriver instance
        base_url: Base search URL
        num_pages: Number of pages to scrape
        delay: Delay between page requests

    Returns:
        List of unique business page URLs
    """
    all_links = []

    for page in range(1, num_pages + 1):
        if page == 1:
            url = base_url
        else:
            url = f"{base_url}&page={page}"

        page_links = extract_links_from_page(driver, url)

        # Add only unique links
        new_links = [link for link in page_links if link not in all_links]
        all_links.extend(new_links)

        print(f"[*] Page {page}/{num_pages}: {len(page_links)} links ({len(new_links)} new) - Total: {len(all_links)}")

        if page < num_pages:
            time.sleep(delay)

    return all_links


def extract_all_data(driver, url):
    """
    Extract ALL business data from a single business page in one visit.

    Extracts: name, type, address, phone, email, website

    Args:
        driver: WebDriver instance
        url: Business page URL

    Returns:
        Dictionary with all business data
    """
    driver.get(url)

    wait = WebDriverWait(driver, ELEMENT_WAIT_TIMEOUT)
    try:
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "h1")))
    except:
        pass

    time.sleep(0.5)

    # Extract name (h1)
    name = safe_extract(driver, "h1")

    # Extract type (h2, filtered)
    business_type = None
    try:
        h2_elements = driver.find_elements(By.CSS_SELECTOR, "h2")
        for h2 in h2_elements:
            text = h2.text.strip()
            if text and "privacy" not in text.lower() and "cookie" not in text.lower():
                if " in " in text or len(text) < 100:
                    business_type = text
                    break
    except:
        pass

    # Extract phone
    phone = safe_extract(driver, "a[href^='tel:']")

    # Extract email
    email = safe_extract(driver, "a[href^='mailto:']")

    # Extract address (button with postal code)
    address = None
    try:
        buttons = driver.find_elements(By.CSS_SELECTOR, "button")
        for btn in buttons:
            text = btn.text.strip()
            if text and re.search(r'\b\d{4}\b', text):
                if "stelle" not in text.lower() and "valutazione" not in text.lower():
                    address = text
                    break
    except:
        pass

    # Extract website (external links only)
    website = None
    try:
        links = driver.find_elements(By.CSS_SELECTOR, "a[data-testid='contact-link']")
        for link in links:
            href = link.get_attribute("href")
            if href and href.startswith("http"):
                # Skip internal local.ch links and WhatsApp
                if "local.ch" not in href and "wa.me" not in href and "whatsapp" not in href:
                    website = href
                    break
    except:
        pass

    return {
        "name": name,
        "type": business_type,
        "address": address,
        "phone": phone,
        "email": email,
        "website": website,
        "source_url": url,
        "scraped_at": datetime.now().isoformat()
    }
