#!/usr/bin/env python3
"""
Relay Mapping Diagnostic Tool
Tests each channel one-by-one to identify which physical relay it controls
Run this to verify your wiring matches the configuration
"""
import lgpio
import time
import sys

# Current configuration
RELAY_PINS = {
    1: 17,   # Channel 1 should control IN1
    2: 27,   # Channel 2 should control IN2
    3: 22,   # Channel 3 should control IN3
    4: 23,   # Channel 4 should control IN4
    5: 24,   # Channel 5 should control IN5
    6: 25,   # Channel 6 should control IN6
    7: 5,    # Channel 7 should control IN7
    8: 6,    # Channel 8 should control IN8
}

def diagnose_mapping():
    """Test each channel and identify which physical relay clicks"""
    print("=" * 60)
    print("RELAY MAPPING DIAGNOSTIC")
    print("=" * 60)
    print("")
    print("This will test each channel one at a time.")
    print("Watch and listen to identify which PHYSICAL relay clicks.")
    print("")
    
    try:
        # Open GPIO
        h = lgpio.gpiochip_open(0)
        print(f"✅ GPIO opened")
        print("")
        
        # Setup all pins to OFF
        for channel, pin in RELAY_PINS.items():
            lgpio.gpio_claim_output(h, pin)
            lgpio.gpio_write(h, pin, 1)  # OFF
        
        print("All relays initialized to OFF")
        print("")
        print("-" * 60)
        
        # Test each channel
        for channel in sorted(RELAY_PINS.keys()):
            pin = RELAY_PINS[channel]
            
            print(f"\n🔍 Testing CHANNEL {channel} (GPIO{pin})")
            print(f"   Expected: Physical relay IN{channel} should click")
            print(f"   Watch which relay actually clicks...")
            
            input(f"\n   Press ENTER to test Channel {channel}...")
            
            # Turn ON
            lgpio.gpio_write(h, pin, 0)
            print(f"   ✓ Channel {channel} turned ON (relay should click now)")
            time.sleep(3)
            
            # Turn OFF
            lgpio.gpio_write(h, pin, 1)
            print(f"   ✓ Channel {channel} turned OFF")
            
            response = input(f"\n   Which physical relay clicked? (1-8): ").strip()
            
            if response == str(channel):
                print(f"   ✅ CORRECT - CH{channel} controls IN{channel}")
            else:
                print(f"   ❌ MISMATCH - CH{channel} controls IN{response}")
                print(f"      Fix: Map channel {channel} to GPIO pin currently on channel {response}")
            
            print("-" * 60)
        
        # Cleanup
        for pin in RELAY_PINS.values():
            lgpio.gpio_free(h, pin)
        lgpio.gpiochip_close(h)
        
        print("\n" + "=" * 60)
        print("DIAGNOSTIC COMPLETE")
        print("=" * 60)
        print("\nIf you found mismatches, update config/config.py:")
        print("Edit the RELAY_PINS dictionary to match your actual wiring")
        print("")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        print("\n⚠️  Make sure you can SEE and HEAR the relay module!")
        print("⚠️  This test will click each relay for 3 seconds\n")
        
        response = input("Ready to start diagnostic? (y/n): ").strip().lower()
        if response == 'y':
            diagnose_mapping()
        else:
            print("Diagnostic cancelled")
    except KeyboardInterrupt:
        print("\n\nDiagnostic interrupted")
        sys.exit(0)
