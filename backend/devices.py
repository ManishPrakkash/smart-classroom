devices = {
    "light1":  3,   # GPIO3 (I2C SCL, free if no I2C devices); 17→slider, 4→1-Wire, 14→UART busy
    "light2": 18,
    "light3": 27,
    "light4": 22,
    "fan1":   23,
    "fan2":   24,
    "fan3":   25,
    "fan4":    5,
}

# Physical push-button switch GPIO input pins (BCM numbering).
# Each button toggles its corresponding relay when pressed.
# Wired with internal pull-up; connect switch between the GPIO pin and GND.
switch_pins = {
    "light1":  6,
    "light2": 12,
    "light3": 13,
    "light4": 16,
    "fan1":   19,
    "fan2":   20,
    "fan3":   21,
    "fan4":   26,
}
