"""
local.ch Scraper - Interactive Console Application
"""

import json
import os
import re
import sys
from urllib.parse import urlparse, unquote

from config import (
    has_proxy_file, ensure_output_dir, get_db_path, BASE_DIR, DATA_DIR,
    DEFAULT_PAGES, DEFAULT_WORKERS, DEFAULT_WORKERS_NO_PROXY,
    DEFAULT_MAX_ERRORS, DEFAULT_DELAY, DEFAULT_PROXY_COOLDOWN
)
from db import init_database, get_stats
from scraper import (
    get_driver, extract_links_paginated,
    load_links_progress, save_links_progress, delete_links_file
)
from proxy import load_proxies, ProxyPool
from worker import run_workers


def list_databases():
    """List available databases in data/ folder."""
    if not os.path.exists(DATA_DIR):
        return []

    databases = []
    for f in os.listdir(DATA_DIR):
        if f.endswith(".db"):
            databases.append(f)

    return sorted(databases)


def print_banner():
    """Print application banner."""
    print("=" * 60)
    print("  local.ch Scraper v1.0")
    print("  Business data extraction tool")
    print("=" * 60)


def list_link_files():
    """List available link files in data/ folder."""
    if not os.path.exists(DATA_DIR):
        return []

    link_files = []
    for f in os.listdir(DATA_DIR):
        if f.endswith("_links.json"):
            link_files.append(f)

    return sorted(link_files)


def print_main_menu():
    """Print main menu options."""
    print("\n  What would you like to do?")
    print()
    print("    1. Start new scrape")
    print("    2. Run export scripts (on existing database)")
    print("    3. Resume/continue link extraction")
    print("    0. Exit")
    print()


def derive_db_name(url):
    """
    Derive database name from URL.

    Example: https://www.local.ch/it/s/Ticino?rid=xxx -> ticino.db
    """
    try:
        # Parse URL path
        parsed = urlparse(url)
        path = parsed.path  # e.g., /it/s/Ticino or /it/s/Mesolcina%20e%20Calanca%20(Regione)

        # Extract region name from path
        parts = path.split("/")
        if len(parts) >= 4 and parts[2] == "s":
            region = unquote(parts[3])  # URL decode
            # Clean up: remove special chars, lowercase
            region = re.sub(r'[^a-zA-Z0-9]', '_', region).lower()
            region = re.sub(r'_+', '_', region).strip('_')
            return f"{region}.db"
    except:
        pass

    return "scraper_data.db"


def prompt_url():
    """Prompt user for base URL."""
    print("\n[Step 1] Enter the local.ch search URL")
    print("  Example: https://www.local.ch/it/s/Ticino?rid=xxx")
    print()

    while True:
        url = input("  Base URL: ").strip()
        if url and "local.ch" in url:
            return url
        print("  [!] Please enter a valid local.ch URL")


def prompt_yes_no(prompt, default=True):
    """Prompt for yes/no input."""
    default_str = "Y/n" if default else "y/N"
    while True:
        response = input(f"  {prompt} [{default_str}]: ").strip().lower()
        if not response:
            return default
        if response in ("y", "yes"):
            return True
        if response in ("n", "no"):
            return False
        print("  [!] Please enter y or n")


def prompt_int(prompt, default, min_val=1, max_val=None):
    """Prompt for integer input."""
    while True:
        response = input(f"  {prompt} [{default}]: ").strip()
        if not response:
            return default
        try:
            value = int(response)
            if value < min_val:
                print(f"  [!] Value must be at least {min_val}")
                continue
            if max_val and value > max_val:
                print(f"  [!] Value must be at most {max_val}")
                continue
            return value
        except ValueError:
            print("  [!] Please enter a valid number")


def prompt_float(prompt, default, min_val=0):
    """Prompt for float input."""
    while True:
        response = input(f"  {prompt} [{default}]: ").strip()
        if not response:
            return default
        try:
            value = float(response)
            if value < min_val:
                print(f"  [!] Value must be at least {min_val}")
                continue
            return value
        except ValueError:
            print("  [!] Please enter a valid number")


def prompt_config():
    """Prompt user for configuration."""
    print("\n[Step 2] Configuration")

    config = {}

    # Pages
    config["pages"] = prompt_int("Pages to scrape", DEFAULT_PAGES, min_val=1)

    # Proxy detection
    if has_proxy_file():
        print(f"\n  [*] Found proxylist.txt")
        use_proxies = prompt_yes_no("Use proxies?", default=True)
    else:
        print(f"\n  [*] No proxylist.txt found - running without proxies")
        use_proxies = False

    config["use_proxies"] = use_proxies

    if use_proxies:
        config["workers"] = prompt_int("Number of workers", DEFAULT_WORKERS, min_val=1, max_val=20)
        config["max_errors"] = prompt_int("Max errors before proxy swap", DEFAULT_MAX_ERRORS, min_val=1)
        config["cooldown"] = prompt_int("Proxy cooldown (seconds)", DEFAULT_PROXY_COOLDOWN, min_val=60)
    else:
        config["workers"] = prompt_int("Number of workers", DEFAULT_WORKERS_NO_PROXY, min_val=1, max_val=3)
        config["max_errors"] = 3

    config["delay"] = prompt_float("Delay between requests (sec)", DEFAULT_DELAY, min_val=0)

    return config


def list_scripts():
    """List available scripts in scripts/ folder."""
    scripts_dir = os.path.join(BASE_DIR, "scripts")
    if not os.path.exists(scripts_dir):
        return []

    scripts = []
    for f in os.listdir(scripts_dir):
        if f.endswith(".py") and not f.startswith("_"):
            scripts.append(f)

    return sorted(scripts)


def run_script(script_name, db_path):
    """Run a script with db_path argument."""
    script_path = os.path.join(BASE_DIR, "scripts", script_name)
    if os.path.exists(script_path):
        print(f"\n[*] Running {script_name}...")
        os.system(f'python "{script_path}" "{db_path}"')
    else:
        print(f"  [!] Script not found: {script_path}")


def prompt_run_scripts(db_path, standalone=False):
    """Prompt user to run post-processing scripts."""
    scripts = list_scripts()

    if not scripts:
        print("\n[*] No scripts found in scripts/ folder")
        return

    if standalone:
        print("\n  Export Scripts")
    else:
        print("\n[Step 5] Post-processing scripts")

    print("  Available scripts:")
    for i, script in enumerate(scripts, 1):
        print(f"    {i}. {script}")
    print(f"    0. Skip")

    while True:
        choice = prompt_int("Select script (0 to skip)", 0, min_val=0, max_val=len(scripts))
        if choice == 0:
            return
        run_script(scripts[choice - 1], db_path)

        if not prompt_yes_no("Run another script?", default=False):
            return


def prompt_select_database():
    """Prompt user to select an existing database."""
    databases = list_databases()

    if not databases:
        print("\n[!] No databases found in data/ folder")
        print("    Run a scrape first to create a database.")
        return None

    print("\n  Available databases:")
    for i, db in enumerate(databases, 1):
        db_path = os.path.join(DATA_DIR, db)
        try:
            stats = get_stats(db_path)
            print(f"    {i}. {db} ({stats['total']} records)")
        except:
            print(f"    {i}. {db}")
    print(f"    0. Back to menu")

    choice = prompt_int("Select database", 0, min_val=0, max_val=len(databases))
    if choice == 0:
        return None

    return os.path.join(DATA_DIR, databases[choice - 1])


def run_export_mode():
    """Run export scripts on existing database."""
    db_path = prompt_select_database()
    if not db_path:
        return

    # Show database stats
    try:
        stats = get_stats(db_path)
        db_name = os.path.basename(db_path)
        print(f"\n  Database: {db_name}")
        print(f"    Total records: {stats['total']}")
        print(f"    With email:    {stats['with_email']}")
        print(f"    With website:  {stats['with_website']}")
        print(f"    With phone:    {stats['with_phone']}")
    except Exception as e:
        print(f"\n[!] Error reading database: {e}")
        return

    # Run export scripts
    prompt_run_scripts(db_path, standalone=True)


def run_scrape_mode():
    """Run full scraping workflow."""
    # Step 1: Get base URL
    base_url = prompt_url()
    db_name = derive_db_name(base_url)
    db_path = get_db_path(db_name)
    print(f"\n  [*] Database: {db_path}")

    # Check for existing links
    existing_progress = load_links_progress(db_name)
    links = None
    start_page = 1

    if existing_progress:
        print(f"\n  [*] Found existing link data:")
        print(f"      Links: {existing_progress['link_count']}")
        print(f"      Pages: {existing_progress['last_page']}/{existing_progress['total_pages']}")
        print(f"      Status: {'Complete' if existing_progress['completed'] else 'Incomplete'}")
        print()
        print("    1. Use existing links (skip extraction)")
        print("    2. Resume extraction (continue from last page)")
        print("    3. Start fresh (delete and re-extract)")
        print()

        choice = prompt_int("Select option", 1, min_val=1, max_val=3)

        if choice == 1:
            # Use existing links
            links = existing_progress['links']
            print(f"\n  [*] Using {len(links)} existing links")
        elif choice == 2:
            # Resume from last page
            start_page = existing_progress['last_page'] + 1
            links = existing_progress['links']
            if existing_progress['completed']:
                print("\n  [*] Link extraction already complete, using existing links")
        elif choice == 3:
            # Start fresh
            delete_links_file(db_name)
            print("\n  [*] Deleted old link data, starting fresh")

    # Step 2: Configuration
    config = prompt_config()

    # Summary
    print("\n" + "-" * 60)
    print("  Configuration Summary:")
    print(f"    URL: {base_url[:50]}...")
    print(f"    Database: {db_name}")
    print(f"    Pages: {config['pages']}")
    print(f"    Workers: {config['workers']}")
    print(f"    Use proxies: {config['use_proxies']}")
    print(f"    Delay: {config['delay']}s")
    if links:
        print(f"    Links: {len(links)} (from file)")
    print("-" * 60)

    if not prompt_yes_no("\nProceed with scraping?", default=True):
        print("\n[*] Cancelled")
        return

    # Step 3: Initialize
    print("\n[Step 3] Initializing...")
    init_database(db_path)
    ensure_output_dir()

    proxy_pool = None
    if config["use_proxies"]:
        proxies = load_proxies()
        proxy_pool = ProxyPool(proxies, cooldown=config.get("cooldown", DEFAULT_PROXY_COOLDOWN))
        status = proxy_pool.status()
        print(f"  [*] Proxy pool: {status['total']} proxies loaded")

    # Step 4: Extract links (if not already loaded)
    if links is None or (existing_progress and not existing_progress['completed'] and start_page > 1):
        if start_page > 1:
            print(f"\n[Step 4] Resuming link extraction from page {start_page}...")
        else:
            print(f"\n[Step 4] Extracting links from {config['pages']} pages...")

        driver = get_driver()  # Use direct connection for link extraction
        try:
            links = extract_links_paginated(
                driver, base_url, config["pages"],
                delay=config["delay"],
                db_name=db_name,
                start_page=start_page,
                existing_links=links
            )
        finally:
            driver.quit()

    if not links:
        print("\n[!] No links extracted. Check the URL and try again.")
        return

    print(f"\n  [*] Total {len(links)} unique links ready for scraping")

    # Step 5: Scrape all data
    print(f"\n[Step 5] Scraping business data...")
    results = run_workers(links, db_path, proxy_pool, config)

    # Step 6: Results
    print(f"\n{'=' * 60}")
    print("[SUCCESS] Scraping complete!")
    print(f"{'=' * 60}")
    print(f"  Time elapsed: {results['elapsed']:.1f}s ({results['elapsed_min']:.1f} min)")
    print(f"\n  Results:")
    print(f"    Inserted: {results['inserted']}")
    print(f"    Skipped:  {results['skipped']}")
    print(f"    Errors:   {results['errors']}")
    if config["use_proxies"]:
        print(f"    Proxy swaps: {results['proxy_swaps']}")

    # Database stats
    stats = get_stats(db_path)
    print(f"\n  Database ({db_name}):")
    print(f"    Total records: {stats['total']}")
    print(f"    With email:    {stats['with_email']}")
    print(f"    With website:  {stats['with_website']}")
    print(f"    With phone:    {stats['with_phone']}")

    # Step 7: Optional scripts
    prompt_run_scripts(db_path)

    print(f"\n{'=' * 60}")
    print("[*] Done!")
    print(f"{'=' * 60}")


def run_resume_mode():
    """Resume or manage link extraction."""
    link_files = list_link_files()

    if not link_files:
        print("\n[!] No link files found in data/ folder")
        print("    Start a new scrape first.")
        return

    print("\n  Available link files:")
    for i, lf in enumerate(link_files, 1):
        lf_path = os.path.join(DATA_DIR, lf)
        try:
            with open(lf_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                status = "Complete" if data['completed'] else f"Page {data['last_page']}/{data['total_pages']}"
                print(f"    {i}. {lf} ({data['link_count']} links, {status})")
        except:
            print(f"    {i}. {lf}")
    print(f"    0. Back to menu")

    choice = prompt_int("Select link file", 0, min_val=0, max_val=len(link_files))
    if choice == 0:
        return

    selected_file = link_files[choice - 1]
    db_name = selected_file.replace('_links.json', '.db')

    progress = load_links_progress(db_name)
    if not progress:
        print("\n[!] Error reading link file")
        return

    print(f"\n  Link file: {selected_file}")
    print(f"    Base URL: {progress['base_url'][:60]}...")
    print(f"    Links: {progress['link_count']}")
    print(f"    Progress: {progress['last_page']}/{progress['total_pages']} pages")
    print(f"    Status: {'Complete' if progress['completed'] else 'Incomplete'}")
    print()
    print("    1. Continue extraction (resume from last page)")
    print("    2. Go straight to scraping (use current links)")
    print("    3. Delete this link file")
    print("    0. Back to menu")
    print()

    action = prompt_int("Select action", 0, min_val=0, max_val=3)

    if action == 0:
        return
    elif action == 1:
        # Resume extraction
        if progress['completed']:
            print("\n[*] Link extraction already complete!")
            if prompt_yes_no("Proceed to scraping?", default=True):
                action = 2
            else:
                return

        if action == 1:  # Still want to resume
            start_page = progress['last_page'] + 1
            print(f"\n[*] Resuming from page {start_page}...")

            driver = get_driver()
            try:
                links = extract_links_paginated(
                    driver, progress['base_url'], progress['total_pages'],
                    delay=DEFAULT_DELAY,
                    db_name=db_name,
                    start_page=start_page,
                    existing_links=progress['links']
                )
                print(f"\n[SUCCESS] Extracted {len(links)} total links")
            except KeyboardInterrupt:
                print("\n\n[*] Interrupted - progress saved")
                return
            finally:
                driver.quit()

            if prompt_yes_no("\nProceed to scraping?", default=True):
                action = 2
                progress = load_links_progress(db_name)  # Reload with new links
            else:
                return

    if action == 2:
        # Go to scraping
        db_path = get_db_path(db_name)
        links = progress['links']

        print(f"\n[*] Starting scrape with {len(links)} links")

        config = prompt_config()
        init_database(db_path)
        ensure_output_dir()

        proxy_pool = None
        if config["use_proxies"]:
            proxies = load_proxies()
            proxy_pool = ProxyPool(proxies, cooldown=config.get("cooldown", DEFAULT_PROXY_COOLDOWN))
            status = proxy_pool.status()
            print(f"  [*] Proxy pool: {status['total']} proxies loaded")

        print(f"\n[*] Scraping business data...")
        results = run_workers(links, db_path, proxy_pool, config)

        print(f"\n{'=' * 60}")
        print("[SUCCESS] Scraping complete!")
        print(f"{'=' * 60}")
        print(f"  Time elapsed: {results['elapsed']:.1f}s ({results['elapsed_min']:.1f} min)")
        print(f"\n  Results:")
        print(f"    Inserted: {results['inserted']}")
        print(f"    Skipped:  {results['skipped']}")
        print(f"    Errors:   {results['errors']}")

        stats = get_stats(db_path)
        print(f"\n  Database ({db_name}):")
        print(f"    Total records: {stats['total']}")
        print(f"    With email:    {stats['with_email']}")
        print(f"    With website:  {stats['with_website']}")
        print(f"    With phone:    {stats['with_phone']}")

        prompt_run_scripts(db_path)

    elif action == 3:
        # Delete link file
        if prompt_yes_no(f"Delete {selected_file}?", default=False):
            delete_links_file(db_name)
            print(f"\n[*] Deleted {selected_file}")


def main():
    """Main entry point."""
    print_banner()
    print_main_menu()

    while True:
        choice = prompt_int("Select option", 1, min_val=0, max_val=3)

        if choice == 0:
            print("\n[*] Goodbye!")
            return
        elif choice == 1:
            run_scrape_mode()
            return
        elif choice == 2:
            run_export_mode()
            # After export, show menu again
            print_banner()
            print_main_menu()
        elif choice == 3:
            run_resume_mode()
            # After resume, show menu again
            print_banner()
            print_main_menu()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[*] Interrupted by user")
        sys.exit(1)
