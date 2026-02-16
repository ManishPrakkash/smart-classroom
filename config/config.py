"""
Configuration module for Smart Classroom system
"""
import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent.parent

# Flask Configuration
class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    DEBUG = False
    TESTING = False
    
    # Session configuration
    SESSION_COOKIE_SECURE = False  # Set to True if using HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Logging
    LOG_DIR = BASE_DIR / 'logs'
    LOG_FILE = LOG_DIR / 'smart_classroom.log'
    LOG_LEVEL = 'INFO'
    
    # GPIO Configuration for Raspberry Pi 5
    GPIO_CHIP = 0  # gpiochip0 for Raspberry Pi 5
    
    # Relay GPIO Pin Mapping (BCM numbering)
    # These pins connect to IN1-IN8 on the relay board
    RELAY_PINS = {
        1: 17,   # IN1 → GPIO17 (Pin 11)
        2: 27,   # IN2 → GPIO27 (Pin 13)
        3: 22,   # IN3 → GPIO22 (Pin 15)
        4: 23,   # IN4 → GPIO23 (Pin 16)
        5: 24,   # IN5 → GPIO24 (Pin 18)
        6: 25,   # IN6 → GPIO25 (Pin 22)
        7: 5,    # IN7 → GPIO5  (Pin 29)
        8: 6,    # IN8 → GPIO6  (Pin 31)
    }
    
    # Relay names for each channel (customizable)
    RELAY_NAMES = {
        1: "Channel 1",
        2: "Channel 2",
        3: "Channel 3",
        4: "Channel 4",
        5: "Channel 5",
        6: "Channel 6",
        7: "Channel 7",
        8: "Channel 8"
    }
    
    # Relay trigger type (0 = ON for active-low relays)
    RELAY_ACTIVE_LOW = True  # True for active-low trigger relays
    
    # Authentication
    DEFAULT_USERNAME = os.environ.get('ADMIN_USERNAME') or 'admin'
    DEFAULT_PASSWORD = os.environ.get('ADMIN_PASSWORD') or 'classroom123'  # Change this!
    
    # Future: Camera Module Configuration (for attendance system)
    CAMERA_ENABLED = False
    CAMERA_RESOLUTION = (640, 480)
    FACE_CASCADE_PATH = '/usr/share/opencv4/haarcascades/haarcascade_frontalface_default.xml'
    ATTENDANCE_DB_PATH = BASE_DIR / 'data' / 'attendance.db'

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    LOG_LEVEL = 'WARNING'

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
