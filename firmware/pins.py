# noinspection PyPackageRequirements
import board
import microcontroller


class Pins:
    BUTTON_A: microcontroller.Pin


class PinsA(Pins):
    LASER_EN = board.D0
    RX = board.D1
    TX = board.D2
    BUTTON_A = board.D4
    BUTTON_B = board.D3
    BUZZER_A = board.D10
    BUZZER_B = board.D6
    PERIPH_EN = board.D5
    SDA = board.D7
    SCL = board.D8
    DRDY = board.D9
