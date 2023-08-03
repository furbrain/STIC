import board

hardware = "phil"

if hardware=="phil":
    # Phil's pinout
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
elif hardware=="brendan":
    # Brendan's pinout
    LASER_EN = board.D0
    RX = board.RX
    TX = board.TX
    BUTTON_A = board.D3
    BUTTON_B = board.D2
    BUZZER_A = board.D8
    BUZZER_B = None
    PERIPH_EN = board.D1
    SDA = board.SDA
    SCL = board.SCL
    DRDY = board.D9
