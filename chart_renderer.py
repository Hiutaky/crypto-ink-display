"""Render mini line charts using Pillow."""

from typing import List, Optional, Tuple
from PIL import Image, ImageDraw, ImageFont


def render_line_chart(
    data: List[Tuple[float, float]],
    width: int = 250,
    height: int = 60,
    line_color: int = 1,
    bg_color: int = 0,
) -> Image.Image:
    """Render a simple line chart from price data.

    Args:
        data: List of (timestamp, price) tuples
        width: Chart width in pixels
        height: Chart height in pixels
        line_color: 1 for black (ink), 0 for white
        bg_color: 0 for white (paper), 1 for black

    Returns:
        PIL Image with the chart.
    """
    if not data or len(data) < 2:
        # Return empty chart with message
        img = Image.new("L", (width, height), bg_color * 255)
        return img

    img = Image.new("L", (width, height), bg_color * 255)
    draw = ImageDraw.Draw(img)

    # Extract prices
    prices = [p for _, p in data]

    # Normalize to chart dimensions with padding
    min_price = min(prices)
    max_price = max(prices)
    price_range = max_price - min_price

    if price_range == 0:
        price_range = 1.0

    padding = 2
    chart_width = width - 2 * padding
    chart_height = height - 2 * padding

    # Draw line
    points = []
    for i, (ts, price) in enumerate(data):
        x = int(padding + (i / (len(data) - 1)) * chart_width)
        y_normalized = (price - min_price) / price_range
        y = int(height - padding - y_normalized * chart_height)
        points.append((x, y))

    # Draw line segments
    for i in range(len(points) - 1):
        draw.line([points[i], points[i + 1]], fill=line_color * 255, width=1)

    return img


def render_price_text(
    symbol: str,
    price: float,
    change_24h: Optional[float] = None,
    font_size: int = 16,
) -> Image.Image:
    """Render price text as an image.

    Args:
        symbol: Crypto symbol (e.g., "BTC")
        price: Current price in USD
        change_24h: 24-hour percentage change (optional)
        font_size: Font size for the text

    Returns:
        PIL Image with the price text.
    """
    # Format price based on magnitude
    if price >= 1000:
        price_str = f"${price:,.0f}"
    elif price >= 1:
        price_str = f"${price:,.2f}"
    else:
        price_str = f"${price:.4f}"

    # Build text with change indicator
    if change_24h is not None:
        if change_24h >= 0:
            change_str = f"▲ +{change_24h:.1f}%"
        else:
            change_str = f"▼ {change_24h:.1f}%"
        text = f"{symbol} {price_str} {change_str}"
    else:
        text = f"{symbol} {price_str}"

    # Estimate image size (rough approximation)
    char_width = font_size * 0.6
    img_width = int(len(text) * char_width) + 10
    img_height = font_size + 4

    img = Image.new("L", (img_width, img_height), 0)
    draw = ImageDraw.Draw(img)

    # Try to use a monospace font if available
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", font_size)
    except (IOError, OSError):
        font = ImageFont.load_default()

    draw.text((5, 0), text, fill=255, font=font)
    return img


def render_full_display(
    symbol: str,
    price: float,
    change_24h: Optional[float],
    chart_data: List[Tuple[float, float]],
    width: int = 296,
    height: int = 128,
) -> Image.Image:
    """Render the complete display for one cryptocurrency.

    Layout:
    - Top row: Symbol + Price + 24h change
    - Bottom area: Mini line chart (last 15 min)

    Args:
        symbol: Crypto symbol
        price: Current price in USD
        change_24h: 24-hour percentage change
        chart_data: Historical price data for chart
        width: Display width
        height: Display height

    Returns:
        PIL Image ready to send to e-ink display.
    """
    # Create as binary 1-bit (black=0/ink, white=255/paper) like Waveshare example
    img = Image.new("1", (height, width), 255)
    draw = ImageDraw.Draw(img)

    # Top section: price info
    try:
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 14)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 10)
    except (IOError, OSError):
        font_large = ImageFont.load_default()
        font_small = font_large

    # Format price
    if price >= 1000:
        price_str = f"${price:,.0f}"
    elif price >= 1:
        price_str = f"${price:,.2f}"
    else:
        price_str = f"${price:.4f}"

    # Change indicator
    if change_24h is not None:
        if change_24h >= 0:
            change_str = f"▲ +{change_24h:.1f}%"
        else:
            change_str = f"▼ {change_24h:.1f}%"
    else:
        change_str = ""

    # Draw symbol and price on top line (black text on white bg)
    draw.text((5, 5), f"{symbol}", fill=0, font=font_large)
    draw.text((60, 5), price_str, fill=0, font=font_large)

    # Draw change on second line (right-aligned)
    if change_str:
        change_width = len(change_str) * 7
        draw.text((width - change_width - 5, 5), change_str, fill=0, font=font_small)

    # Separator line
    draw.line([(0, 30), (width, 30)], fill=0, width=1)

    # Chart area: draw directly on the main image (all black-on-white like reference)
    chart_height = height - 40
    
    if chart_data and len(chart_data) >= 2:
        prices = [p for _, p in chart_data]
        min_price = min(prices)
        max_price = max(prices)
        price_range = max_price - min_price
        if price_range == 0:
            price_range = 1.0
        
        padding = 2
        chart_w = width - 2 * padding
        chart_h = height - 45  # Leave room for label
        
        points = []
        for i, (ts, price) in enumerate(chart_data):
            x = int(padding + (i / (len(chart_data) - 1)) * chart_w)
            y_norm = (price - min_price) / price_range
            y = int(35 + chart_h - y_norm * chart_h)
            points.append((x, y))
        
        for i in range(len(points) - 1):
            draw.line([points[i], points[i+1]], fill=0, width=1)

    # Chart label - use 0 for max contrast on binary display
    draw.text((5, height - 12), "Last 15 min", fill=0, font=font_small)

    return img
