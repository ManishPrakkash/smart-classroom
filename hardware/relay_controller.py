"""
GPIO Relay Controller for Raspberry Pi 5
Uses lgpio library for reliable GPIO control
"""
import lgpio
import logging
import time
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class RelayController:
    """Controls 8-channel relay module via GPIO"""
    
    def __init__(self, gpio_chip: int, relay_pins: Dict[int, int], active_low: bool = True):
        """
        Initialize relay controller
        
        Args:
            gpio_chip: GPIO chip number (0 for Raspberry Pi 5)
            relay_pins: Dictionary mapping relay channel (1-8) to GPIO pin number
            active_low: True if relay triggers on LOW signal (common for most modules)
        """
        self.gpio_chip = gpio_chip
        self.relay_pins = relay_pins
        self.active_low = active_low
        self.handle: Optional[int] = None
        self.relay_states: Dict[int, bool] = {}
        
        # Initialize all relays to OFF state
        for channel in self.relay_pins.keys():
            self.relay_states[channel] = False
        
        logger.info(f"RelayController initialized with {len(relay_pins)} channels")
    
    def initialize(self):
        """Initialize GPIO chip and configure pins as outputs"""
        try:
            # Open GPIO chip
            self.handle = lgpio.gpiochip_open(self.gpio_chip)
            logger.info(f"Opened GPIO chip {self.gpio_chip}, handle: {self.handle}")
            
            # Configure all relay pins as outputs and set to OFF
            for channel, pin in self.relay_pins.items():
                lgpio.gpio_claim_output(self.handle, pin)
                # Set initial state to OFF
                off_value = 1 if self.active_low else 0
                lgpio.gpio_write(self.handle, pin, off_value)
                logger.debug(f"Channel {channel} (GPIO{pin}) initialized to OFF")
            
            logger.info("All relay channels initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize GPIO: {e}")
            return False
    
    def set_relay(self, channel: int, state: bool) -> bool:
        """
        Set relay state
        
        Args:
            channel: Relay channel number (1-8)
            state: True for ON, False for OFF
            
        Returns:
            bool: Success status
        """
        if channel not in self.relay_pins:
            logger.error(f"Invalid relay channel: {channel}")
            return False
        
        if self.handle is None:
            logger.error("GPIO not initialized")
            return False
        
        try:
            pin = self.relay_pins[channel]
            
            # For active-low relays: 0 = ON, 1 = OFF
            # For active-high relays: 1 = ON, 0 = OFF
            gpio_value = 0 if (state and self.active_low) or (not state and not self.active_low) else 1
            
            lgpio.gpio_write(self.handle, pin, gpio_value)
            self.relay_states[channel] = state
            
            state_str = "ON" if state else "OFF"
            logger.info(f"Relay {channel} (GPIO{pin}) set to {state_str}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to set relay {channel}: {e}")
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
        logger.info("Turning off all relays")
        for channel in self.relay_pins.keys():
            self.set_relay(channel, False)
    
    def all_on(self):
        """Turn on all relays"""
        logger.info("Turning on all relays")
        for channel in self.relay_pins.keys():
            self.set_relay(channel, True)
    
    def cleanup(self):
        """Cleanup GPIO resources"""
        try:
            if self.handle is not None:
                # Turn off all relays before cleanup
                self.all_off()
                time.sleep(0.1)  # Brief delay to ensure relays switch off
                
                # Free GPIO pins
                for pin in self.relay_pins.values():
                    lgpio.gpio_free(self.handle, pin)
                
                # Close chip handle
                lgpio.gpiochip_close(self.handle)
                self.handle = None
                
                logger.info("GPIO cleanup completed")
        except Exception as e:
            logger.error(f"Error during GPIO cleanup: {e}")
    
    def __enter__(self):
        """Context manager entry"""
        self.initialize()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.cleanup()
