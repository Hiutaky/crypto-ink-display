"""Fetch cryptocurrency prices and market data from CoinGecko API."""

import time
import logging
from typing import Dict, List, Optional, Tuple

import requests

logger = logging.getLogger(__name__)


class PriceFetcher:
    """Fetches crypto prices and historical data from CoinGecko."""

    BASE_URL = "https://api.coingecko.com/api/v3"
    TIMEOUT = 10
    MAX_RETRIES = 3

    def __init__(self, crypto_ids: List[str], vs_currency: str = "usd"):
        self.crypto_ids = crypto_ids
        self.vs_currency = vs_currency
        self._cache: Dict[str, float] = {}
        self._last_update: Optional[float] = None

    def fetch_prices(self) -> Dict[str, float]:
        """Fetch current prices for all configured cryptocurrencies.

        Returns:
            Dictionary mapping crypto ID to price in USD.
        """
        ids_str = ",".join(self.crypto_ids)
        url = f"{self.BASE_URL}/simple/price"
        params = {
            "ids": ids_str,
            "vs_currencies": self.vs_currency,
            "include_24hr_change": "true",
        }

        try:
            response = requests.get(url, params=params, timeout=self.TIMEOUT)
            response.raise_for_status()
            data = response.json()

            prices = {}
            for crypto_id in self.crypto_ids:
                if crypto_id in data and self.vs_currency in data[crypto_id]:
                    prices[crypto_id] = data[crypto_id][self.vs_currency]
                else:
                    logger.warning(f"No price found for {crypto_id}")

            self._cache.update(prices)
            self._last_update = time.time()
            return prices

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch prices: {e}")
            # Return cached prices if available
            if self._cache:
                logger.info("Returning cached prices")
                return dict(self._cache)
            raise

    def get_cached_prices(self) -> Dict[str, float]:
        """Return last known prices from cache."""
        return dict(self._cache)

    def should_refresh(self, interval_seconds: int = 60) -> bool:
        """Check if price refresh is needed based on interval."""
        if self._last_update is None:
            return True
        elapsed = time.time() - self._last_update
        return elapsed >= interval_seconds

    def fetch_market_chart(self, crypto_id: str, minutes: int = 15) -> List[Tuple[float, float]]:
        """Fetch market chart data for a cryptocurrency.

        Args:
            crypto_id: CoinGecko ID of the cryptocurrency
            minutes: Number of minutes of historical data to fetch

        Returns:
            List of (timestamp, price) tuples.
        """
        url = f"{self.BASE_URL}/coins/{crypto_id}/market_chart"
        params = {
            "vs_currency": self.vs_currency,
            "interval": "15m",  # CoinGecko's finest granularity for free tier
        }

        try:
            response = requests.get(url, params=params, timeout=self.TIMEOUT)
            response.raise_for_status()
            data = response.json()

            prices_data = data.get("prices", [])
            if not prices_data:
                logger.warning(f"No chart data for {crypto_id}")
                return []

            # Filter to last N minutes (each point is 15 min apart)
            now = time.time() * 1000  # CoinGecko uses ms timestamps
            cutoff = now - (minutes * 60 * 1000)
            recent_data = [(ts, price) for ts, price in prices_data if ts >= cutoff]

            # If we don't have enough points, return last few available
            if len(recent_data) < 2:
                recent_data = prices_data[-4:]

            return recent_data

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch chart for {crypto_id}: {e}")
            return []
