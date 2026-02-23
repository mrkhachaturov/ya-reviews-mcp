"""Signal handling for graceful shutdown."""
import logging
import signal
import sys

logger = logging.getLogger("ya-reviews")


def setup_signal_handlers() -> None:
    """Register SIGTERM and SIGINT handlers for graceful shutdown."""
    def _handle_signal(sig: int, frame: object) -> None:
        logger.info("Received signal %s, shutting down...", signal.Signals(sig).name)
        sys.exit(0)

    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)
