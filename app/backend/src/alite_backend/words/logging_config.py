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
    logging.basicConfig(
        filename=log_file_loc,  # type: ignore
        format="%(asctime)s.%(msecs)03d %(name)s %(levelname)s:%(message)s",
        datefmt="%Y%m%d %H:%M:%S",
        encoding="utf-8",
        level=logging.DEBUG,
    )
    """
    # Define the format for your log messages
    log_format = "%(asctime)s.%(msecs)03d %(name)s %(levelname)s:%(message)s"
    date_format = "%Y%m%d %H:%M:%S"
    encoding = "utf-8"

    # Create a formatter
    formatter = logging.Formatter(log_format)

    # Get the root logger
    root_logger = logging.getLogger()

    # Set the minimum level of logs to capture (e.g., INFO, DEBUG)
    root_logger.setLevel(logging.DEBUG)

    # Avoid adding duplicate handlers if this function is called more than once
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    # Create a handler to write log messages to the console (standard output)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    # Add the handler to the root logger
    root_logger.addHandler(console_handler)

    # You could also add a FileHandler here to log to a file
    file_handler = logging.FileHandler(LOG_FILE_LOC)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    logging.info("Logging configured successfully.")
