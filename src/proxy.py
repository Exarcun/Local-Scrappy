"""
Proxy management for local.ch scraper
"""

import time
import threading
from config import PROXY_FILE, DEFAULT_PROXY_COOLDOWN


def load_proxies(filepath=None):
    """
    Load proxies from file.

    Args:
        filepath: Path to proxy file (default: proxylist.txt)

    Returns:
        List of proxy strings "host:port"
    """
    filepath = filepath or PROXY_FILE
    try:
        with open(filepath, "r") as f:
            proxies = [line.strip() for line in f if line.strip()]
        return proxies
    except FileNotFoundError:
        return []


class ProxyPool:
    """
    Thread-safe proxy pool with hot/cold management.

    Cold proxies: Available for use
    Hot proxies: Recently failed, in cooldown period
    """

    def __init__(self, proxies, cooldown=None):
        """
        Initialize proxy pool.

        Args:
            proxies: List of proxy strings
            cooldown: Seconds before hot proxy becomes cold (default: 300)
        """
        self.lock = threading.Lock()
        self.cold_proxies = list(proxies)
        self.hot_proxies = {}  # proxy -> timestamp when marked hot
        self.cooldown = cooldown or DEFAULT_PROXY_COOLDOWN
        self.assigned = {}  # worker_id -> proxy

    def _refresh_cooled_proxies(self):
        """Move cooled-down proxies from hot back to cold."""
        now = time.time()
        cooled = []

        for proxy, timestamp in list(self.hot_proxies.items()):
            if now - timestamp >= self.cooldown:
                cooled.append(proxy)

        for proxy in cooled:
            del self.hot_proxies[proxy]
            if proxy not in self.cold_proxies:
                self.cold_proxies.append(proxy)

    def get_proxy(self, worker_id):
        """
        Get an available proxy for a worker.

        Args:
            worker_id: Worker identifier

        Returns:
            Proxy string or None if no proxies available
        """
        with self.lock:
            self._refresh_cooled_proxies()

            # Return current assigned proxy if still cold
            if worker_id in self.assigned:
                current = self.assigned[worker_id]
                if current in self.cold_proxies:
                    return current

            # Get a new cold proxy
            if not self.cold_proxies:
                return None

            proxy = self.cold_proxies.pop(0)
            self.assigned[worker_id] = proxy
            return proxy

    def mark_hot(self, proxy, worker_id):
        """
        Mark a proxy as hot (failed).

        Args:
            proxy: Proxy string
            worker_id: Worker identifier
        """
        with self.lock:
            self.hot_proxies[proxy] = time.time()
            if proxy in self.cold_proxies:
                self.cold_proxies.remove(proxy)
            if worker_id in self.assigned and self.assigned[worker_id] == proxy:
                del self.assigned[worker_id]
            print(f"    [PROXY] Marked {proxy} as HOT (cooldown: {self.cooldown}s)")

    def status(self):
        """
        Get current pool status.

        Returns:
            Dict with cold and hot counts
        """
        with self.lock:
            self._refresh_cooled_proxies()
            return {
                "cold": len(self.cold_proxies),
                "hot": len(self.hot_proxies),
                "total": len(self.cold_proxies) + len(self.hot_proxies)
            }

    def has_available(self):
        """Check if any proxies are available."""
        with self.lock:
            self._refresh_cooled_proxies()
            return len(self.cold_proxies) > 0
