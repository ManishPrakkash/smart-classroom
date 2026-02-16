"""
REST API Routes for Smart Classroom Control
"""
from flask import Blueprint, jsonify, request
from functools import wraps
import logging

logger = logging.getLogger(__name__)

# Create API blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api')

# Relay controller instance (set by main app)
relay_controller = None

def init_api(controller):
    """Initialize API with relay controller"""
    global relay_controller
    relay_controller = controller
    logger.info("API initialized with relay controller")

def require_auth(f):
    """Decorator to require authentication for API endpoints"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user is authenticated (session-based)
        from flask import session
        if not session.get('authenticated'):
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated_function

@api_bp.route('/status', methods=['GET'])
def get_status():
    """Get system status and all relay states"""
    try:
        if relay_controller is None:
            return jsonify({'error': 'Hardware not initialized'}), 500
        
        states = relay_controller.get_all_states()
        
        # Get relay names from config
        from flask import current_app
        relay_names = current_app.config.get('RELAY_NAMES', {})
        
        # Build response with relay information
        relays = []
        for channel, state in sorted(states.items()):
            relays.append({
                'channel': channel,
                'name': relay_names.get(channel, f'Relay {channel}'),
                'state': state,
                'state_text': 'ON' if state else 'OFF'
            })
        
        return jsonify({
            'success': True,
            'relays': relays,
            'total_channels': len(states)
        })
    
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/relay/<int:channel>', methods=['GET'])
@require_auth
def get_relay_state(channel):
    """Get state of specific relay channel"""
    try:
        if relay_controller is None:
            return jsonify({'error': 'Hardware not initialized'}), 500
        
        state = relay_controller.get_relay_state(channel)
        
        if state is None:
            return jsonify({'error': f'Invalid channel: {channel}'}), 400
        
        from flask import current_app
        relay_names = current_app.config.get('RELAY_NAMES', {})
        
        return jsonify({
            'success': True,
            'channel': channel,
            'name': relay_names.get(channel, f'Relay {channel}'),
            'state': state,
            'state_text': 'ON' if state else 'OFF'
        })
    
    except Exception as e:
        logger.error(f"Error getting relay {channel} state: {e}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/relay/<int:channel>', methods=['POST'])
@require_auth
def set_relay_state(channel):
    """Set state of specific relay channel"""
    try:
        if relay_controller is None:
            return jsonify({'error': 'Hardware not initialized'}), 500
        
        data = request.get_json()
        
        if data is None or 'state' not in data:
            return jsonify({'error': 'Missing state parameter'}), 400
        
        state = bool(data['state'])
        
        success = relay_controller.set_relay(channel, state)
        
        if not success:
            return jsonify({'error': f'Failed to set relay {channel}'}), 500
        
        from flask import current_app
        relay_names = current_app.config.get('RELAY_NAMES', {})
        
        return jsonify({
            'success': True,
            'channel': channel,
            'name': relay_names.get(channel, f'Relay {channel}'),
            'state': state,
            'state_text': 'ON' if state else 'OFF'
        })
    
    except Exception as e:
        logger.error(f"Error setting relay {channel}: {e}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/relay/<int:channel>/toggle', methods=['POST'])
@require_auth
def toggle_relay(channel):
    """Toggle state of specific relay channel"""
    try:
        if relay_controller is None:
            return jsonify({'error': 'Hardware not initialized'}), 500
        
        success = relay_controller.toggle_relay(channel)
        
        if not success:
            return jsonify({'error': f'Failed to toggle relay {channel}'}), 500
        
        state = relay_controller.get_relay_state(channel)
        
        from flask import current_app
        relay_names = current_app.config.get('RELAY_NAMES', {})
        
        return jsonify({
            'success': True,
            'channel': channel,
            'name': relay_names.get(channel, f'Relay {channel}'),
            'state': state,
            'state_text': 'ON' if state else 'OFF'
        })
    
    except Exception as e:
        logger.error(f"Error toggling relay {channel}: {e}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/relay/all/on', methods=['POST'])
@require_auth
def all_relays_on():
    """Turn on all relays"""
    try:
        if relay_controller is None:
            return jsonify({'error': 'Hardware not initialized'}), 500
        
        relay_controller.all_on()
        states = relay_controller.get_all_states()
        
        return jsonify({
            'success': True,
            'message': 'All relays turned ON',
            'states': states
        })
    
    except Exception as e:
        logger.error(f"Error turning on all relays: {e}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/relay/all/off', methods=['POST'])
@require_auth
def all_relays_off():
    """Turn off all relays"""
    try:
        if relay_controller is None:
            return jsonify({'error': 'Hardware not initialized'}), 500
        
        relay_controller.all_off()
        states = relay_controller.get_all_states()
        
        return jsonify({
            'success': True,
            'message': 'All relays turned OFF',
            'states': states
        })
    
    except Exception as e:
        logger.error(f"Error turning off all relays: {e}")
        return jsonify({'error': str(e)}), 500

# Future: Camera/Attendance API endpoints (placeholder for future expansion)
@api_bp.route('/camera/status', methods=['GET'])
@require_auth
def camera_status():
    """Get camera module status (future feature)"""
    return jsonify({
        'success': True,
        'enabled': False,
        'message': 'Camera module not yet implemented'
    })

@api_bp.route('/attendance/mark', methods=['POST'])
@require_auth
def mark_attendance():
    """Mark attendance via face detection (future feature)"""
    return jsonify({
        'success': False,
        'message': 'Attendance system not yet implemented'
    })
