"""Display driver for Waveshare 2.13" e-ink display (SPI).

Uses the epd-library package: https://pypi.org/project/epd-library/
"""

import time
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class EPDDisplay:
    """Driver for Waveshare 2.9" e-ink display."""

    def __init__(self, width=250, height=128):
        self.width = width
        self.height = height
        self._initialized = False
        self._epd = None

        # Try to import the epd-library package (V2 variant)
        try:
            from epdlibrary.epd2in13_v2 import EPD as WaveshareEPD
            self._epd = WaveshareEPD()
            logger.info("Using epd-library for 2.13\" V2 display")
        except ImportError:
            # Try standard version
            try:
                from epdlibrary.epd2in13 import EPD as WaveshareEPD
                self._epd = WaveshareEPD()
                logger.info("Using epd-library for 2.13\" display")
            except ImportError:
                # Try waveshare-epd as fallback
                try:
                    from waveshare_epd.epd2in13 import EPD as WaveshareEPD
                    self._epd = WaveshareEPD()
                    logger.info("Using waveshare-epd for 2.13\" display")
                except ImportError:
                    logger.warning("No e-paper library found, using mock display")

    def init(self):
        """Initialize the display."""
        if self._initialized:
            return

        if self._epd is not None:
            try:
                self._epd.init()
                logger.info("Display initialized")
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
                self._epd.Clear()
                logger.debug("Display cleared")
            except Exception as e:
                logger.error(f"Failed to clear display: {e}")
        else:
            logger.debug("Mock display cleared")

    def update(self, image):
        """Update the display with a PIL Image.

        Args:
            image: PIL Image in 'L' mode (grayscale) matching display dimensions.
        """
        if not self._initialized:
            self.init()

        if self._epd is not None:
            try:
                # Convert to byte array for waveshare library
                img_data = list(image.getdata())
                # Waveshare expects 1 bit per pixel (0=black, 1=white)
                binary_data = [0 if p < 128 else 1 for p in img_data]

                self._epd.display(binary_data)
                logger.debug("Display updated")
            except Exception as e:
                logger.error(f"Failed to update display: {e}")
        else:
            # Mock: save image to file for testing
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
        if self._initialized:
            try:
                self.sleep()
            except Exception:
                pass
            self._initialized = False
