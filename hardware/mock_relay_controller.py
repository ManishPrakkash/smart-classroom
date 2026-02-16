"""
Mock Relay Controller for Testing Without Hardware
Simulates relay behavior for development/testing on PC
"""
import logging
import time
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class MockRelayController:
    """Mock controller that simulates relay behavior without GPIO hardware"""
    
    def __init__(self, gpio_chip: int, relay_pins: Dict[int, int], active_low: bool = True):
        """
        Initialize mock relay controller
        
        Args:
            gpio_chip: GPIO chip number (ignored in mock mode)
            relay_pins: Dictionary mapping relay channel (1-8) to GPIO pin number
            active_low: True if relay triggers on LOW signal (ignored in mock mode)
        """
        self.gpio_chip = gpio_chip
        self.relay_pins = relay_pins
        self.active_low = active_low
        self.handle = 999  # Mock handle
        self.relay_states: Dict[int, bool] = {}
        
        # Initialize all relays to OFF state
        for channel in self.relay_pins.keys():
            self.relay_states[channel] = False
        
        logger.warning("=" * 60)
        logger.warning("MOCK MODE: Running without GPIO hardware")
        logger.warning("This is for testing the web interface only")
        logger.warning("No actual relays will be controlled")
        logger.warning("=" * 60)
        logger.info(f"MockRelayController initialized with {len(relay_pins)} channels")
    
    def initialize(self):
        """Initialize mock GPIO (simulation only)"""
        try:
            logger.info(f"Mock: Opened GPIO chip {self.gpio_chip}, handle: {self.handle}")
            
            # Simulate GPIO initialization
            for channel, pin in self.relay_pins.items():
                logger.debug(f"Mock: Channel {channel} (GPIO{pin}) initialized to OFF")
            
            logger.info("Mock: All relay channels initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Mock initialization error: {e}")
            return False
    
    def set_relay(self, channel: int, state: bool) -> bool:
        """
        Simulate setting relay state
        
        Args:
            channel: Relay channel number (1-8)
            state: True for ON, False for OFF
            
        Returns:
            bool: Success status
        """
        if channel not in self.relay_pins:
            logger.error(f"Invalid relay channel: {channel}")
            return False
        
        try:
            pin = self.relay_pins[channel]
            self.relay_states[channel] = state
            
            state_str = "ON" if state else "OFF"
            # Simulate relay click sound
            click = "🔊 *CLICK*" if state else "🔇 *click*"
            logger.info(f"Mock: Relay {channel} (GPIO{pin}) set to {state_str} {click}")
            
            # Simulate hardware delay
            time.sleep(0.05)
            return True
            
        except Exception as e:
            logger.error(f"Failed to set mock relay {channel}: {e}")
            return False
    
    def get_relay_state(self, channel: int) -> Optional[bool]:
        """
        Get current relay state
        
        Args:
            channel: Relay channel number (1-8)
            
        Returns:
            bool or None: Current state (True=ON, False=OFF) or None if invalid
        """
        return self.relay_states.get(channel)
    
    def get_all_states(self) -> Dict[int, bool]:
        """Get all relay states"""
        return self.relay_states.copy()
    
    def toggle_relay(self, channel: int) -> bool:
        """
        Toggle relay state
        
        Args:
            channel: Relay channel number (1-8)
            
        Returns:
            bool: Success status
        """
        current_state = self.get_relay_state(channel)
        if current_state is None:
            return False
        
        new_state = not current_state
        return self.set_relay(channel, new_state)
    
    def all_off(self):
        """Turn off all relays"""
        logger.info("Mock: Turning off all relays")
        for channel in self.relay_pins.keys():
            self.set_relay(channel, False)
    
    def all_on(self):
        """Turn on all relays"""
        logger.info("Mock: Turning on all relays")
        for channel in self.relay_pins.keys():
            self.set_relay(channel, True)
    
    def cleanup(self):
        """Cleanup mock GPIO resources"""
        try:
            logger.info("Mock: Cleaning up hardware...")
            self.all_off()
            time.sleep(0.1)
            
            for pin in self.relay_pins.values():
                logger.debug(f"Mock: Freed GPIO{pin}")
            
            logger.info("Mock: Cleanup completed")
            
        except Exception as e:
            logger.error(f"Mock cleanup error: {e}")
    
    def __enter__(self):
        """Context manager entry"""
        self.initialize()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.cleanup()
