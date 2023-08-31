import adafruit_logging
import os
import storage

logger = adafruit_logging.getLogger()
try:
    os.stat("DEBUG")
    logger.setLevel(adafruit_logging.DEBUG)
except IOError:
    logger.setLevel(adafruit_logging.WARNING)
if not storage.getmount("/").readonly:
    logger.addHandler(adafruit_logging.FileHandler("log.txt"))
logger.debug("Starting log")

INFO = adafruit_logging.INFO
WARNING = adafruit_logging.WARNING
DEBUG = adafruit_logging.DEBUG
ERROR = adafruit_logging.ERROR