from gpiozero import OutputDevice
from time import sleep

pins = [17, 18, 27, 22, 23, 24, 25, 5]

relays = [OutputDevice(pin, active_high=False) for pin in pins]

try:
    while True:
        for i, relay in enumerate(relays, start=1):
            print(f"Relay {i} ON")
            relay.on()
            sleep(1)

            print(f"Relay {i} OFF")
            relay.off()
            sleep(0.5)

except KeyboardInterrupt:
    print("Stopping relay test...")
