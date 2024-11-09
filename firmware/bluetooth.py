import time
import sys

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
    batt_service = BatteryService()
    advertisement = ProvideServicesAdvertisement(disto,
                                                 batt_service)

    def __init__(self):
        self.ble = BLERadio()
        logger.info("Starting bluetooth")
        logger.debug(self.ble.connections)
        self.ble.name = version.get_short_name()
        logger.debug(f"BLE name is {self.ble.name}")
        if not self.ble.connected and not self.ble.advertising:
            if sys.platform=='nRF52840':
                logger.debug("BLE advertising high power")
                self.ble._adapter.start_advertising(bytes(self.advertisement),tx_power=8)
            else:
                logger.debug("BLE advertising")
                self.ble.start_advertising(BluetoothServices.advertisement)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.deinit()

    async def disto_background_task(self, callback=None):
        await self.disto.background_task(callback)

    def set_battery_level(self, voltage):
        self.batt_service.level = utils.convert_voltage_to_progress(voltage, 100)

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

