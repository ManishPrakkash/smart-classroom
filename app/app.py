"""
Smart Classroom Flask Application
Main application factory and initialization
"""
import os
import sys
import logging
from pathlib import Path
from flask import Flask, render_template, request, session, redirect, url_for, jsonify
import atexit

# Add parent directory to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import configuration
from config.config import config

# Auto-detect hardware availability
MOCK_MODE = False
try:
    import lgpio
    # lgpio available, use real hardware controller
    from hardware.relay_controller import RelayController
    MOCK_MODE = False
except ImportError:
    # lgpio not available, use mock controller for testing
    from hardware.mock_relay_controller import MockRelayController as RelayController
    MOCK_MODE = True

# Import API
from api.routes import api_bp, init_api

# Global relay controller instance
relay_controller = None

def setup_logging(app):
    """Configure application logging"""
    log_dir = app.config['LOG_DIR']
    log_dir.mkdir(exist_ok=True)
    
    log_file = app.config['LOG_FILE']
    log_level = getattr(logging, app.config['LOG_LEVEL'])
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info("Logging configured")
    logger.info(f"Log file: {log_file}")

def init_hardware(app):
    """Initialize GPIO and relay controller"""
    global relay_controller
    
    logger = logging.getLogger(__name__)
    
    # Show mode warning if in mock mode
    if MOCK_MODE:
        logger.warning("=" * 70)
        logger.warning("RUNNING IN MOCK MODE (No GPIO Hardware)")
        logger.warning("This is for testing the web interface on PC/Mac/Linux")
        logger.warning("Relay states will be simulated - no actual hardware control")
        logger.warning("To use real hardware, run on Raspberry Pi with lgpio installed")
        logger.warning("=" * 70)
    
    try:
        relay_controller = RelayController(
            gpio_chip=app.config['GPIO_CHIP'],
            relay_pins=app.config['RELAY_PINS'],
            active_low=app.config['RELAY_ACTIVE_LOW']
        )
        
        if relay_controller.initialize():
            mode = "MOCK MODE" if MOCK_MODE else "HARDWARE MODE"
            logger.info(f"Hardware initialized successfully ({mode})")
            # Initialize API with controller
            init_api(relay_controller)
            return True
        else:
            logger.error("Failed to initialize hardware")
            return False
            
    except Exception as e:
        logger.error(f"Hardware initialization error: {e}")
        return False

def cleanup_hardware():
    """Cleanup GPIO on application exit"""
    global relay_controller
    logger = logging.getLogger(__name__)
    
    if relay_controller is not None:
        logger.info("Cleaning up hardware...")
        relay_controller.cleanup()
        logger.info("Hardware cleanup completed")

def create_app(config_name='default'):
    """Application factory"""
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Setup logging
    setup_logging(app)
    
    logger = logging.getLogger(__name__)
    logger.info(f"Starting Smart Classroom Application (Config: {config_name})")
    
    # Initialize hardware
    init_hardware(app)
    
    # Register cleanup handler
    atexit.register(cleanup_hardware)
    
    # Register blueprints
    app.register_blueprint(api_bp)
    
    # Web routes
    @app.route('/')
    def index():
        """Main dashboard page"""
        if not session.get('authenticated'):
            return redirect(url_for('login'))
        return render_template('index.html')
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        """Login page"""
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            
            if (username == app.config['DEFAULT_USERNAME'] and 
                password == app.config['DEFAULT_PASSWORD']):
                session['authenticated'] = True
                session['username'] = username
                logger.info(f"User {username} logged in")
                return redirect(url_for('index'))
            else:
                logger.warning(f"Failed login attempt for username: {username}")
                return render_template('login.html', error='Invalid credentials')
        
        return render_template('login.html')
    
    @app.route('/logout')
    def logout():
        """Logout user"""
        username = session.get('username', 'Unknown')
        session.clear()
        logger.info(f"User {username} logged out")
        return redirect(url_for('login'))
    
    @app.errorhandler(404)
    def not_found(e):
        """404 error handler"""
        return jsonify({'error': 'Not found'}), 404
    
    @app.errorhandler(500)
    def server_error(e):
        """500 error handler"""
        logger.error(f"Server error: {e}")
        return jsonify({'error': 'Internal server error'}), 500
    
    return app

if __name__ == '__main__':
    # Determine configuration from environment
    env = os.environ.get('FLASK_ENV', 'development')
    config_name = 'production' if env == 'production' else 'development'
    
    # Create and run app
    app = create_app(config_name)
    
    # Run on all interfaces to allow network access
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=app.config['DEBUG']
    )
