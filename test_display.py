"""Standalone connectivity test for the Waveshare 2.13" V2 e-ink display.

Runs FOUR test pages in sequence (5 seconds each), full refresh every time:

  PAGE 1 - all WHITE        -> expect: white screen
  PAGE 2 - all BLACK        -> expect: completely BLACK screen
  PAGE 3 - 50/50 checker    -> expect: checkerboard pattern
  PAGE 4 - border + "OK"    -> expect: thick border with big "OK" text

How to read the result:
  - page 2 never goes black  -> hardware/SPI/refresh problem (check wiring,
                                reset line, or that the display is the V2)
  - pages 2-3 fine, page 4 missing -> image content/buffer size problem
  - everything fine          -> driver is good, the app issue is in the
                                render pipeline (dimensions/polarity)

Usage on the Pi:
    python3 test_display.py
"""

import importlib.util
import logging
import os
import sys
import time

from PIL import Image, ImageDraw, ImageFont

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("test_display")

WIDTH = 250
HEIGHT = 128
PAGE_DELAY = 5  # seconds each page stays visible


# ---------------------------------------------------------------------------
# EPD loading - try the same import the driver uses, then common fallbacks
# ---------------------------------------------------------------------------

def _find_class(module):
    """Find the EPD class inside a module (names vary between Waveshare layouts)."""
    for name in ("EPD_2IN13_V2", "EPD2IN13_V2", "EPD_2IN13", "EPD"):
        cls = getattr(module, name, None)
        if cls is not None and hasattr(cls, "init"):
            return cls
    # last resort: any class in the module that looks like an EPD controller
    for name in dir(module):
        obj = getattr(module, name)
        if isinstance(obj, type) and hasattr(obj, "init") and hasattr(obj, "display"):
            return obj
    return None


def load_epd():
    """Load the e-ink controller or return None (mock mode)."""
    # 1) what the main driver uses
    try:
        from waveshare_epd import epd2in13_V2  # noqa: N813
        cls = _find_class(epd2in13_V2)
        if cls is not None:
            epd = cls()
            logger.info("Loaded waveshare_epd.epd2in13_V2 class %s", cls.__name__)
            return epd
        logger.warning("waveshare_epd.epd2in13_V2 imported but no EPD class found")
    except Exception as e:
        logger.info("waveshare_epd import failed (%s), trying fallbacks", e)

    # 2) Waveshare repo cloned on the Pi (various layouts)
    candidates = [
        os.path.expanduser("~/e-Paper/lib/e-Paper/EPD_2IN13_V2.py"),
        os.path.expanduser("~/e-Paper/RaspberryPi_JetsonNano/python/lib/e-Paper/EPD_2IN13_V2.py"),
        os.path.expanduser("~/e-Paper/RaspberryPi_JetsonNano/python/lib/e-Paper/epd2in13_V2.py"),
        "lib/e-Paper/EPD_2IN13_V2.py",
        "e-Paper/lib/e-Paper/EPD_2IN13_V2.py",
    ]
    for path in candidates:
        if not os.path.exists(path):
            continue
        try:
            spec = importlib.util.spec_from_file_location("epd_module_under_test", path)
            if spec is None or spec.loader is None:
                logger.warning("Could not create spec for %s", path)
                continue
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            cls = _find_class(mod)
            if cls is not None:
                epd = cls()
                logger.info("Loaded %s (class %s)", path, cls.__name__)
                return epd
            logger.warning("%s exists but no EPD class found in it", path)
        except Exception as e:
            logger.warning("Could not load %s: %s", path, e)

    return None


def _method(epd, *names):
    """Return the first available method among `names` (Waveshare naming varies)."""
    for name in names:
        fn = getattr(epd, name, None)
        if callable(fn):
            return fn
    return None


# ---------------------------------------------------------------------------
# Test page builders
# ---------------------------------------------------------------------------

def page_all_white():
    # Waveshare uses (height, width) order - unusual vs PIL's (width, height)!
    return Image.new("1", (HEIGHT, WIDTH), 255)


def page_all_black():
    return Image.new("1", (HEIGHT, WIDTH), 0)


def page_checker():
    img = Image.new("L", (HEIGHT, WIDTH), 255)
    d = ImageDraw.Draw(img)
    for y in range(0, HEIGHT, 4):
        for x in range(0, WIDTH, 4):
            color = 0 if ((x // 4 + y // 4) % 2) == 0 else 255
            d.rectangle([x, y, x + 3, y + 3], fill=color)
    return img.convert("1")


def page_ok():
    img = Image.new("L", (WIDTH, HEIGHT), 255)
    d = ImageDraw.Draw(img)
    # thick border so orientation is obvious
    d.rectangle([0, 0, WIDTH - 1, HEIGHT - 1], outline=0, width=6)
    # big OK in the middle
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 64)
    except (IOError, OSError):
        font = ImageFont.load_default()
    d.text((WIDTH // 2, HEIGHT // 2), "OK", fill=0, font=font, anchor="mm")
    # small arrow so we can check orientation (points right)
    d.polygon([(WIDTH - 30, HEIGHT // 2 - 8), (WIDTH - 14, HEIGHT // 2),
              (WIDTH - 30, HEIGHT // 2 + 8)], fill=0)
    return img.convert("1")


# ---------------------------------------------------------------------------
# Display helper
# ---------------------------------------------------------------------------

def show(epd, img, label):
    """Send one page to the display (or save it in mock mode)."""
    if epd is None:
        ts = int(time.time())
        path = f"/tmp/epd-test-{label}-{ts}.png"
        img.save(path)
        logger.info("[MOCK] %s -> saved to %s", label, path)
        return

    init_fn = _method(epd, "init")
    getbuf_fn = _method(epd, "getBuffer", "getbuffer")
    display_fn = _method(epd, "display")

    try:
        # V2 API: init(FULL) does a full refresh; PART won't reliably repaint
        # the whole screen, so force a full refresh for every test page.
        full_const = None
        for const in ("FULL", "FULL_UPDATE", "FULL_REFRESH"):
            if hasattr(epd, const):
                full_const = getattr(epd, const)
                break
        if full_const is not None:
            init_fn(full_const)
        else:
            init_fn()

        buf = getbuf_fn(img)
        logger.info("%s: buffer %d bytes (expect %d for %dx%d)",
                    label, len(buf), WIDTH * HEIGHT // 8, WIDTH, HEIGHT)
        display_fn(buf)
    except Exception as e:
        logger.error("%s FAILED: %s", label, e)


def main():
    epd = load_epd()
    if epd is None:
        logger.warning("NO e-paper library found - running in MOCK mode "
                       "(images saved to /tmp, nothing will appear on screen)")

    sleep_fn = _method(epd, "sleep") if epd else None
    close_fn = _method(epd, "close", "Close") if epd else None

    pages = [
        ("page1-white", page_all_white(), "expect: WHITE"),
        ("page2-black", page_all_black(), "expect: ALL BLACK"),
        ("page3-checker", page_checker(), "expect: CHECKERBOARD"),
        ("page4-ok", page_ok(), "expect: BORDER + 'OK'"),
    ]

    try:
        for i, (name, img, expected) in enumerate(pages, 1):
            logger.info("--- page %d/4: %s (%s) ---", i, name, expected)
            show(epd, img, name)
            if i < len(pages):
                # give the full refresh time to settle + let the user look
                time.sleep(3)
    except KeyboardInterrupt:
        logger.info("Interrupted")
    finally:
        if sleep_fn:
            try:
                sleep_fn()
            except Exception:
                pass
        if close_fn:
            try:
                close_fn()
            except Exception:
                pass

    print()
    print("Test done. Tell me what you saw on each of the 4 pages:")
    print("  1) white?  2) all black?  3) checkerboard?  4) border+OK?")
    sys.exit(0)


if __name__ == "__main__":
    main()
