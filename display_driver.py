"""Display driver for Waveshare 2.9" e-ink display (SPI).

This module provides a simple interface to drive the Waveshare 2.9" e-paper
display connected via SPI on Raspberry Pi Zero.
"""

import time
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class EPDDisplay:
    """Driver for Waveshare 2.9" e-ink display."""

    def __init__(self, width=296, height=128):
        self.width = width
        self.height = height
        self._initialized = False

        # Try to import the waveshare library
        try:
            from waveshare_epd.epd2in9 import EPD as WaveshareEPD
            self._epd = WaveshareEPD()
            logger.info("Using waveshare-epd library")
        except ImportError:
            logger.warning("waveshare-epd not installed, using mock display")
            self._epd = None

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
