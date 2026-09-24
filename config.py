"""Configuration for crypto ink display."""

# Cryptocurrencies to track (CoinGecko IDs)
CRYPTO_IDS = [
    "bitcoin",
    "ethereum",
    "solana",
    "ripple",
    "cardano",
    "polkadot",
    "dogecoin"
]

# Display symbols for each crypto
CRYPTO_SYMBOLS = {
    "bitcoin": "BTC",
    "ethereum": "ETH",
    "solana": "SOL",
    "ripple": "XRP",
    "cardano": "ADA",
    "polkadot": "DOT",
    "dogecoin": "DOGE"
}

# Rotation interval (seconds per coin)
ROTATION_INTERVAL = 10

# Price refresh interval (seconds)
PRICE_REFRESH_INTERVAL = 60

# Chart data points to show (last N minutes)
CHART_MINUTES = 15

# Display dimensions (Waveshare 2.13")
DISPLAY_WIDTH = 250
DISPLAY_HEIGHT = 128
