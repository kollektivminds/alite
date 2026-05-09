import logging
import sys
import os
from dotenv import load_dotenv

load_dotenv()

LOG_FILE_LOC = os.getenv("LOG_LOC")
print(f"logging files at {LOG_FILE_LOC}")

def setup_logging():
    """
    Configures the root logger for the application.
    This should be called only ONCE at the application's entry point.
    """
    # Define the format for your log messages
    log_format = "%(asctime)s.%(msecs)03d %(name)s %(levelname)s:%(message)s"
    date_format = "%Y%m%d %H:%M:%S"

    # Create a formatter
    formatter = logging.Formatter(fmt=log_format, datefmt=date_format)

    # Get the root logger
    root_logger = logging.getLogger()

    # Set the minimum level of logs to capture
    root_logger.setLevel(logging.DEBUG)

    # Avoid adding duplicate handlers if this function is called more than once
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    # 1. CONSOLE HANDLER (Outputs to terminal)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # 2. FILE HANDLER (Outputs to your .env location)
    if LOG_FILE_LOC:
        # Create the directory if it doesn't exist so it doesn't crash
        os.makedirs(os.path.dirname(LOG_FILE_LOC), exist_ok=True)
        
        file_handler = logging.FileHandler(LOG_FILE_LOC, encoding="utf-8")
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    else:
        print("WARNING: LOG_LOC not found in .env. File logging is disabled.")