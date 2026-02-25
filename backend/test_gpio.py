#!/usr/bin/env python3
"""
GPIO Diagnostic Test Script
Tests GPIO functionality on Raspberry Pi to diagnose connectivity issues

Usage:
  python test_gpio.py
"""

import os
import sys
import time

print("=" * 60)
print("GPIO Diagnostic Test")
print("=" * 60)

# Check environment
print(f"\n[1] Environment:")
print(f"    USE_MOCK_GPIO: {os.getenv('USE_MOCK_GPIO', 'not set')}")
print(f"    Python: {sys.version}")

# Check if running on Raspberry Pi
try:
    with open("/proc/cpuinfo", "r") as f:
        is_pi = "Raspberry Pi" in f.read()
        print(f"    Raspberry Pi: {'YES' if is_pi else 'NO'}")
except:
    print(f"    Raspberry Pi: NO (could not read /proc/cpuinfo)")
    is_pi = False

# Import gpiozero
print(f"\n[2] Importing gpiozero...")
try:
    from gpiozero import Device, OutputDevice
    print(f"    ✓ gpiozero imported successfully")
except ImportError as e:
    print(f"    ✗ Failed to import gpiozero: {e}")
    sys.exit(1)

# Check pin factory
print(f"\n[3] Pin Factory:")
try:
    Device.ensure_pin_factory()
    factory_name = type(Device.pin_factory).__name__
    print(f"    Active factory: {factory_name}")
    
    if "Mock" in factory_name:
        print(f"    ⚠️  WARNING: Using MockFactory (GPIO will not control real pins)")
        print(f"    To fix: export USE_MOCK_GPIO=0")
    else:
        print(f"    ✓ Real GPIO factory active")
except Exception as e:
    print(f"    ✗ Pin factory error: {e}")
    sys.exit(1)

# Test GPIO pin access
print(f"\n[4] Testing GPIO Pin Access:")
TEST_PIN = 17  # light1 from devices.py

try:
    print(f"    Creating OutputDevice on GPIO {TEST_PIN} (active_high=False)...")
    relay = OutputDevice(TEST_PIN, active_high=False)
    print(f"    ✓ GPIO {TEST_PIN} initialized")
    
    # Test on/off
    print(f"\n[5] Testing GPIO Control:")
    print(f"    Turning relay ON (GPIO LOW)...")
    relay.on()
    print(f"    State: {'ACTIVE' if relay.is_active else 'INACTIVE'}")
    print(f"    Value: {relay.value}")
    time.sleep(2)
    
    print(f"\n    Turning relay OFF (GPIO HIGH)...")
    relay.off()
    print(f"    State: {'ACTIVE' if relay.is_active else 'INACTIVE'}")
    print(f"    Value: {relay.value}")
    time.sleep(2)
    
    # Toggle test
    print(f"\n[6] Toggle Test (watch your device):")
    for i in range(3):
        print(f"    Toggle {i+1}/3: ON")
        relay.on()
        time.sleep(1)
        print(f"    Toggle {i+1}/3: OFF")
        relay.off()
        time.sleep(1)
    
    print(f"\n✓ GPIO test completed successfully!")
    print(f"\nIf your relay/device didn't respond:")
    print(f"  1. Check physical wiring (GPIO {TEST_PIN} → Relay IN)")
    print(f"  2. Check relay module power supply (VCC, GND)")
    print(f"  3. Try active_high=True instead (some relays need this)")
    print(f"  4. Verify GPIO permissions: sudo usermod -a -G gpio $USER")
    print(f"  5. For RPi 3/4: sudo systemctl status pigpiod")
    print(f"  6. For RPi 5: pip list | grep lgpio")
    
    relay.close()
    
except PermissionError:
    print(f"    ✗ Permission denied!")
    print(f"    Fix: sudo usermod -a -G gpio $USER")
    print(f"         Then logout and login again")
except Exception as e:
    print(f"    ✗ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
