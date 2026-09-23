"""Main application: crypto price display with rotation."""

import time
import logging
from typing import Dict, Optional

import config
from price_fetcher import PriceFetcher
from chart_renderer import render_full_display
from display_driver import EPDDisplay

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__main__)


class CryptoDisplayApp:
    """Main application that rotates crypto prices on e-ink display."""

    def __init__(self):
        self.fetcher = PriceFetcher(config.CRYPTO_IDS)
        self.display = EPDDisplay(config.DISPLAY_WIDTH, config.DISPLAY_HEIGHT)
        self.prices: Dict[str, float] = {}
        self.changes_24h: Dict[str, Optional[float]] = {}
        self.current_index = 0

    def fetch_all_data(self):
        """Fetch prices and chart data for all cryptocurrencies."""
        logger.info("Fetching prices...")
        self.prices = self.fetcher.fetch_prices()

        # Fetch 24h changes (CoinGecko simple/price supports this)
        ids_str = ",".join(config.CRYPTO_IDS)
        import requests
        url = f"{self.fetcher.BASE_URL}/simple/price"
        params = {
            "ids": ids_str,
            "vs_currencies": "usd",
            "include_24hr_change": "true",
        }
        try:
            response = requests.get(url, params=params, timeout=self.fetcher.TIMEOUT)
            response.raise_for_status()
            data = response.json()
            for crypto_id in config.CRYPTO_IDS:
                if crypto_id in data and "usd_24h_change" in data[crypto_id]:
                    self.changes_24h[crypto_id] = data[crypto_id]["usd_24h_change"]
        except Exception as e:
            logger.warning(f"Failed to fetch 24h changes: {e}")

    def render_current(self) -> None:
        """Render and display the current cryptocurrency."""
        crypto_id = config.CRYPTO_IDS[self.current_index]
        symbol = config.CRYPTO_SYMBOLS.get(crypto_id, crypto_id.upper())

        price = self.prices.get(crypto_id)
        if price is None:
            logger.warning(f"No price for {crypto_id}, skipping")
            return

        change_24h = self.changes_24h.get(crypto_id)

        # Fetch chart data for this crypto
        logger.info(f"Fetching chart for {symbol}...")
        chart_data = self.fetcher.fetch_market_chart(crypto_id, config.CHART_MINUTES)

        # Render display
        logger.info(f"Rendering {symbol} at ${price:,.2f}")
        image = render_full_display(
            symbol=symbol,
            price=price,
            change_24h=change_24h,
            chart_data=chart_data,
            width=config.DISPLAY_WIDTH,
            height=config.DISPLAY_HEIGHT,
        )

        # Update display
        self.display.update(image)

    def run(self):
        """Main loop: rotate through cryptocurrencies."""
        logger.info("Starting crypto ink display...")
        self.display.init()

        try:
            while True:
                # Check if we need to refresh prices
                if self.fetcher.should_refresh(config.PRICE_REFRESH_INTERVAL):
                    self.fetch_all_data()

                # Render current crypto
                self.render_current()

                # Wait for rotation interval
                logger.info(f"Waiting {config.ROTATION_INTERVAL}s before next...")
                time.sleep(config.ROTATION_INTERVAL)

                # Advance to next crypto
                self.current_index = (self.current_index + 1) % len(config.CRYPTO_IDS)

        except KeyboardInterrupt:
            logger.info("Interrupted by user")
        finally:
            self.display.close()
            logger.info("Display closed")


if __name__ == "__main__":
    app = CryptoDisplayApp()
    app.run()
