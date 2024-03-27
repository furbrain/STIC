import time

import _bleio
from adafruit_ble import BLERadio
from adafruit_ble.advertising.standard import ProvideServicesAdvertisement
import caveble
from adafruit_ble.services.standard import BatteryService

from . import utils
from .debug import logger

from . import version


class BluetoothServices:
    disto = caveble.SurveyProtocolService()
    advertisement = ProvideServicesAdvertisement(disto)

    def __init__(self):
        self.ble = BLERadio()
        logger.info("Starting bluetooth")
        logger.debug(self.ble.connections)
        self.ble.name = version.get_short_name()
        logger.debug(f"BLE name is {self.ble.name}")
        if not self.ble.connected and not self.ble.advertising:
            logger.debug("BLE advertising")
            self.ble.start_advertising(BluetoothServices.advertisement)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.deinit()

    async def disto_background_task(self, callback=None):
        await self.disto.background_task(callback)

    @property
    def connected(self):
        return self.ble.connected

    def pending_count(self):
        return self.disto.pending()

    def disconnect(self):
        for c in self.ble.connections:
            c.disconnect()

    @staticmethod
    def forget():
        _bleio.adapter.erase_bonding()

    def deinit(self):
        if self.ble.advertising:
            logger.debug("Stopping BT advertisement")
            self.ble.stop_advertising()
        self.ble.stop_scan()
        time.sleep(0.1)

