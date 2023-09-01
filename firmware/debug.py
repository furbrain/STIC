import adafruit_logging
import os
# noinspection PyPackageRequirements
import storage

logger = adafruit_logging.getLogger()
files = os.listdir()
if "DEBUG" in files:
    logger.setLevel(adafruit_logging.DEBUG)
elif "INFO" in files:
    logger.setLevel(adafruit_logging.INFO)
else:
    logger.setLevel(adafruit_logging.WARNING)
if not storage.getmount("/").readonly:
    logger.addHandler(adafruit_logging.FileHandler("log.txt"))
logger.debug("Starting log")

INFO = adafruit_logging.INFO
WARNING = adafruit_logging.WARNING
DEBUG = adafruit_logging.DEBUG
ERROR = adafruit_logging.ERROR
