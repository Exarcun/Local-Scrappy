"""
Parallel worker execution for local.ch scraper
"""

import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from selenium.common.exceptions import WebDriverException, TimeoutException

from scraper import get_driver, extract_all_data
from db import save_business


# Shared counters
counters = {
    "inserted": 0,
    "skipped": 0,
    "errors": 0,
    "proxy_swaps": 0
}
counters_lock = threading.Lock()


def reset_counters():
    """Reset all counters."""
    global counters
    with counters_lock:
        counters = {
            "inserted": 0,
            "skipped": 0,
            "errors": 0,
            "proxy_swaps": 0
        }


def get_counters():
    """Get current counter values."""
    with counters_lock:
        return dict(counters)


def divide_links(links, num_workers):
    """
    Divide links evenly among workers.

    Args:
        links: List of URLs
        num_workers: Number of workers

    Returns:
        List of link chunks
    """
    chunk_size = len(links) // num_workers
    remainder = len(links) % num_workers

    chunks = []
    start = 0
    for i in range(num_workers):
        end = start + chunk_size + (1 if i < remainder else 0)
        chunks.append(links[start:end])
        start = end

    return chunks


def worker(worker_id, links, db_path, proxy_pool, config):
    """
    Worker function with proxy hot-swap capability.

    Args:
        worker_id: Worker identifier
        links: List of URLs to process
        db_path: Path to SQLite database
        proxy_pool: ProxyPool instance or None
        config: Configuration dict

    Returns:
        Tuple of (worker_id, inserted, skipped, errors)
    """
    global counters

    local_inserted = 0
    local_skipped = 0
    local_errors = 0
    local_swaps = 0

    driver = None
    current_proxy = None
    consecutive_errors = 0
    i = 0

    max_errors = config.get("max_errors", 3)
    delay = config.get("delay", 0.3)

    while i < len(links):
        # Get or swap proxy if needed
        if driver is None or (proxy_pool and consecutive_errors >= max_errors):
            # Close old driver if exists
            if driver:
                try:
                    driver.quit()
                except:
                    pass
                driver = None

            # Mark current proxy as hot if we had errors
            if proxy_pool and current_proxy and consecutive_errors >= max_errors:
                proxy_pool.mark_hot(current_proxy, worker_id)
                local_swaps += 1
                with counters_lock:
                    counters["proxy_swaps"] += 1

            # Get new proxy (or None if no proxy mode)
            if proxy_pool:
                retry_count = 0
                while retry_count < 10:
                    current_proxy = proxy_pool.get_proxy(worker_id)
                    if current_proxy:
                        break
                    print(f"[W{worker_id}] Waiting for cold proxy...")
                    time.sleep(30)
                    retry_count += 1

                if not current_proxy:
                    print(f"[W{worker_id}] No proxies available, stopping")
                    break
            else:
                current_proxy = None

            # Start new browser
            try:
                proxy_str = current_proxy if current_proxy else "direct"
                print(f"[W{worker_id}] Starting with {proxy_str}")
                driver = get_driver(current_proxy)
                consecutive_errors = 0
            except Exception as e:
                print(f"[W{worker_id}] Failed to start browser: {e}")
                if proxy_pool and current_proxy:
                    proxy_pool.mark_hot(current_proxy, worker_id)
                current_proxy = None
                continue

        # Process current link
        url = links[i]
        try:
            business = extract_all_data(driver, url)

            if save_business(db_path, business):
                local_inserted += 1
                with counters_lock:
                    counters["inserted"] += 1
                print(f"[W{worker_id}] [{i+1}/{len(links)}] Inserted: {business['name']}")
            else:
                local_skipped += 1
                with counters_lock:
                    counters["skipped"] += 1

            consecutive_errors = 0
            i += 1
            time.sleep(delay)

        except (WebDriverException, TimeoutException) as e:
            consecutive_errors += 1
            local_errors += 1
            with counters_lock:
                counters["errors"] += 1
            error_msg = str(e)[:80]
            print(f"[W{worker_id}] [{i+1}/{len(links)}] Network error ({consecutive_errors}/{max_errors}): {error_msg}")

            if proxy_pool and consecutive_errors >= max_errors:
                print(f"[W{worker_id}] Too many errors, swapping proxy...")
            elif not proxy_pool:
                # No proxy mode - just retry after delay
                time.sleep(2)
                if consecutive_errors >= max_errors:
                    consecutive_errors = 0
                    i += 1  # Skip this link after max retries

        except Exception as e:
            local_errors += 1
            with counters_lock:
                counters["errors"] += 1
            print(f"[W{worker_id}] [{i+1}/{len(links)}] ERROR: {e}")
            i += 1

    # Cleanup
    if driver:
        try:
            driver.quit()
        except:
            pass

    print(f"[Worker {worker_id}] DONE - Inserted: {local_inserted}, Skipped: {local_skipped}, Errors: {local_errors}, Swaps: {local_swaps}")
    return worker_id, local_inserted, local_skipped, local_errors


def run_workers(links, db_path, proxy_pool, config):
    """
    Run parallel workers to scrape links.

    Args:
        links: List of URLs to process
        db_path: Path to SQLite database
        proxy_pool: ProxyPool instance or None
        config: Configuration dict

    Returns:
        Dict with results
    """
    num_workers = config.get("workers", 1)
    reset_counters()

    # Divide links among workers
    link_chunks = divide_links(links, num_workers)

    print(f"\n[*] Dividing {len(links)} links among {num_workers} workers:")
    for i, chunk in enumerate(link_chunks):
        print(f"    Worker {i}: {len(chunk)} links")

    print(f"\n[*] Starting {num_workers} workers...")
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = []
        for i in range(num_workers):
            future = executor.submit(worker, i, link_chunks[i], db_path, proxy_pool, config)
            futures.append(future)

        # Wait for all workers to complete
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"[ERROR] Worker failed: {e}")

    elapsed = time.time() - start_time

    results = get_counters()
    results["elapsed"] = elapsed
    results["elapsed_min"] = elapsed / 60

    return results
