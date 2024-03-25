try:
    # noinspection PyUnresolvedReferences
    from typing import Optional
    from abc import abstractmethod
except ImportError:
    from .stubs import abstractmethod

try:
    # try to load using 9.0 style, fall back to 8.x style
    from busdisplay import BusDisplay
except ImportError:
    from displayio import Display as BusDisplay

from fruity_menu.menu import Menu


class DisplayBase:
    oled: BusDisplay
    inverted: bool

    @abstractmethod
    def refresh(self):
        pass

    @abstractmethod
    def show_start_screen(self):
        pass

    @abstractmethod
    def update_measurement(self, leg, reading_index, show_extents):
        pass

    @abstractmethod
    def set_bt_connected(self, connected):
        pass

    @abstractmethod
    def set_bt_pending_count(self, count):
        pass

    @abstractmethod
    def set_batt_level(self, voltage):
        pass

    def get_menu(self):
        return Menu(self.oled, self.oled.height, self.oled.width, False, "Menu")

    @abstractmethod
    def show_info(self, text, clean=False):
        pass

    @abstractmethod
    def sleep(self, wake=False):
        pass

    @abstractmethod
    def show_group(self, group):
        pass

    @abstractmethod
    def show_big_info(self, text):
        pass

    @abstractmethod
    def clear_memory(self):
        pass

    @abstractmethod
    def deinit(self):
        pass
