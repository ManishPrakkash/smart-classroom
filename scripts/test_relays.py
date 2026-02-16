#!/usr/bin/env python3
"""
Simple relay test script
Tests individual relay channels on Raspberry Pi 5
"""
import lgpio
import time
import sys

# GPIO pins for relays (BCM numbering)
RELAY_PINS = {
    1: 17,   # IN1
    2: 18,   # IN2
    3: 27,   # IN3
    4: 22,   # IN4
    5: 23,   # IN5
    6: 24,   # IN6
    7: 25,   # IN7
    8: 5,    # IN8
}

def test_relays():
    """Test all relay channels"""
    print("=" * 50)
    print("Smart Classroom - Relay Test")
    print("=" * 50)
    print("")
    
    try:
        # Open GPIO chip
        h = lgpio.gpiochip_open(0)
        print(f"✅ GPIO chip opened (handle: {h})")
        print("")
        
        # Setup all pins
        for channel, pin in RELAY_PINS.items():
            lgpio.gpio_claim_output(h, pin)
            lgpio.gpio_write(h, pin, 1)  # OFF (active-low)
            print(f"Channel {channel} (GPIO{pin:2d}) - Configured")
        
        print("")
        print("Testing each relay (2 seconds ON, 1 second OFF)...")
        print("Watch for relay clicks and LED indicators")
        print("")
        
        # Test each relay
        for channel, pin in RELAY_PINS.items():
            print(f"Testing Channel {channel} (GPIO{pin})...", end=" ")
            sys.stdout.flush()
            
            # Turn ON (LOW for active-low relay)
            lgpio.gpio_write(h, pin, 0)
            print("ON", end=" ")
            sys.stdout.flush()
            time.sleep(2)
            
            # Turn OFF (HIGH)
            lgpio.gpio_write(h, pin, 1)
            print("OFF ✓")
            time.sleep(1)
        
        print("")
        print("All relays OFF - Test complete!")
        
        # Cleanup
        for pin in RELAY_PINS.values():
            lgpio.gpio_free(h, pin)
        
        lgpio.gpiochip_close(h)
        print("")
        print("=" * 50)
        print("✅ Test completed successfully!")
        print("=" * 50)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Check wiring connections")
        print("2. Verify GPIO permissions: sudo usermod -a -G gpio $USER")
        print("3. Reboot if permissions were just added")
        sys.exit(1)

if __name__ == "__main__":
    try:
        test_relays()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(0)
