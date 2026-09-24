"""Display driver for Waveshare 2.13" V2 e-ink display (SPI).

Uses waveshare_epd library from: https://github.com/waveshareteam/e-Paper
Install on Pi: git clone https://github.com/waveshareteam/e-Paper.git
Then copy lib/python to project or add to PYTHONPATH.
"""

import time
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class EPDDisplay:
    """Driver for Waveshare 2.13" V2 e-ink display."""

    def __init__(self, width=250, height=128):
        self.width = width
        self.height = height
        self._initialized = False
        self._epd = None

        # Import waveshare_epd library (installed from Waveshare GitHub repo)
        try:
            from waveshare_epd import epd2in13_V2
            self._epd_module = epd2in13_V2
            self._epd = epd2in13_V2.EPD()
            logger.info("Using waveshare_epd for 2.13\" V2 display")
        except ImportError as e:
            logger.warning(f"waveshare_epd not found, using mock display ({e})")

    def init(self):
        """Initialize the display."""
        if self._initialized:
            return

        if self._epd is not None:
            try:
                # V2 requires update mode parameter - match Waveshare example pattern
                self._epd.init(self._epd.FULL_UPDATE)
                self._epd.Clear(0xFF)  # Clear before first display (like reference example)
                logger.info("Display initialized and cleared")
            except Exception as e:
                logger.error(f"Failed to initialize display: {e}")
                raise
        else:
            logger.info("Mock display initialized")

        self._initialized = True

    def clear(self):
        """Clear the display."""
        if not self._initialized:
            self.init()

        if self._epd is not None:
            try:
                self._epd.Clear(0xFF)
                logger.debug("Display cleared")
            except Exception as e:
                logger.error(f"Failed to clear display: {e}")
        else:
            logger.debug("Mock display cleared")

    def update(self, image):
        """Update the display with a PIL Image."""
        if self._epd is not None:
            try:
                # Convert to 1-bit for e-ink (0=black/ink, 255=white/paper)
                img_1bit = image.convert('1')

                logger.info(f"Displaying image {img_1bit.size} mode={img_1bit.mode}")

                buffer = self._epd.getbuffer(img_1bit)
                # Match Waveshare example: init(FULL_UPDATE) then display()
                self._epd.init(self._epd.FULL_UPDATE)
                self._epd.display(buffer)
                time.sleep(0.5)  # Small delay after display
                logger.debug("Display updated")
            except Exception as e:
                logger.error(f"Failed to update display: {e}")
        else:
            import os
            timestamp = int(time.time())
            filename = f"/tmp/crypto-ink-mock-{timestamp}.png"
            image.save(filename)
            logger.info(f"Mock display updated, saved to {filename}")

    def sleep(self):
        """Put the display to sleep."""
        if self._epd is not None:
            try:
                self._epd.sleep()
                logger.info("Display sleeping")
            except Exception as e:
                logger.error(f"Failed to put display to sleep: {e}")

    def close(self):
        """Clean up and release resources."""
        if self._epd is not None:
            try:
                # Clear display before sleeping (like reference example)
                self._epd.init(self._epd.FULL_UPDATE)
                self._epd.Clear(0xFF)
                logger.info("Display cleared")

                self.sleep()
                logger.info("Display sleeping")

                # Proper cleanup of GPIO and SPI resources
                from waveshare_epd import epd2in13_V2
                epd2in13_V2.epdconfig.module_exit(cleanup=True)
                logger.info("Module exited cleanly")
            except Exception as e:
                logger.error(f"Failed to close display: {e}")
        self._initialized = False