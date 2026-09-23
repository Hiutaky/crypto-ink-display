# Crypto Ink Display

Raspberry Pi Zero e-ink display showing live crypto prices with rotation.

## Features
- Tracks 7 cryptocurrencies: BTC, ETH, SOL, XRP, ADA, DOT, DOG
- Rotates every 10 seconds (full cycle: 70s)
- Shows price + 24h change + mini line chart (last 15 min)
- Uses CoinGecko API (free tier)
- Auto-starts via systemd service

## Hardware
- Raspberry Pi Zero / Zero 2 W
- Waveshare 2.9" e-ink display (296x128, SPI)

## Setup
```bash
# Clone and install dependencies
git clone https://github.com/Hiutaky/crypto-ink-display.git
cd crypto-ink-display
pip3 install -r requirements.txt

# Run manually to test
python3 main.py

# Enable auto-start
sudo cp systemd/crypto-ink.service /etc/systemd/system/
sudo systemctl enable crypto-ink
```

## Configuration
Edit `config.py` to change:
- List of cryptocurrencies to track
- Rotation interval (seconds per coin)
- Price refresh interval
- Display settings
