"""
REST API Routes for Smart Classroom Control
"""
from flask import Blueprint, jsonify, request, current_app
from functools import wraps
import logging
import json
import uuid
import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# Create API blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api')

# Relay controller instance (set by main app)
relay_controller = None

def init_api(controller, app):
    """Initialize API with relay controller and setup scheduler"""
    global relay_controller
    relay_controller = controller
    
    # Register background task
    if hasattr(app, 'scheduler'):
        app.scheduler.add_job(id='check_schedules', func=check_schedules_job, trigger='interval', seconds=30)
        logger.info("Background schedule checker registered (30s interval)")
    
    logger.info("API initialized with relay controller")

def get_db_path():
    return Path(current_app.root_path).parent / 'schedules.json'

def load_schedules():
    path = get_db_path()
    if not path.exists():
        return []
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading schedules: {e}")
        return []

def save_schedules(schedules):
    try:
        with open(get_db_path(), 'w') as f:
            json.dump(schedules, f, indent=4)
    except Exception as e:
        logger.error(f"Error saving schedules: {e}")

def check_schedules_job():
    """Background task to execute schedules"""
    # We need an app context for this because of relay_controller and config
    # Flask-APScheduler handles context for us usually if registered via init_app
    try:
        from app.app import relay_controller
        if relay_controller is None:
            return

        now = datetime.datetime.now()
        current_time = now.strftime("%H:%M")
        current_day = now.strftime("%a") # Mon, Tue, etc.

        schedules = []
        # We need a way to access current_app here. 
        # Since this runs in a separate thread, we might need a manual context or use app instance
        # For simplicity, let's assume it has access to the global relay_controller
        
        # Load from file directly to avoid context issues
        db_path = Path(__file__).parent.parent / 'schedules.json'
        if not db_path.exists():
            return
            
        with open(db_path, 'r') as f:
            schedules = json.load(f)

        for s in schedules:
            if not s.get('enabled', True):
                continue
            
            # Check days
            days = s.get('days', [])
            if current_day not in days and 'Daily' not in days:
                continue

            # Check time
            if s.get('time') == current_time:
                # To prevent double triggering in the same minute, we should track last run
                # But with 30s interval it might trigger twice. 
                # Let's check seconds to be precision or track last run ID.
                
                # Check if already ran in this minute
                last_run = s.get('last_run')
                if last_run == now.strftime("%Y-%m-%d %H:%M"):
                    continue

                logger.info(f"Executing schedule: {s.get('name')} ({s.get('action')})")
                
                # Perform action
                action = s.get('action') # 'on' or 'off'
                state = True if action == 'on' else False
                channels = s.get('channels', [])
                
                for ch in channels:
                    relay_controller.set_relay(ch, state)
                
                # Update last run
                s['last_run'] = now.strftime("%Y-%m-%d %H:%M")
                
        # Save updated schedules (with last_run)
        with open(db_path, 'w') as f:
            json.dump(schedules, f, indent=4)

    except Exception as e:
        print(f"Schedule Execution Error: {e}")

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

# Scheduling API
@api_bp.route('/schedules', methods=['GET'])
@require_auth
def get_schedules():
    """List all schedules"""
    return jsonify({
        'success': True,
        'schedules': load_schedules()
    })

@api_bp.route('/schedules', methods=['POST'])
@require_auth
def add_schedule():
    """Create a new schedule"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate required fields
        required = ['name', 'channels', 'action', 'time', 'days']
        for field in required:
            if field not in data:
                return jsonify({'error': f'Missing field: {field}'}), 400

        schedules = load_schedules()
        
        new_schedule = {
            'id': str(uuid.uuid4()),
            'name': data['name'],
            'channels': data['channels'], # List of ints
            'action': data['action'], # 'on' or 'off'
            'time': data['time'], # "HH:MM"
            'days': data['days'], # List of strings ["Mon", "Tue"] or ["Daily"]
            'enabled': True,
            'created_at': datetime.datetime.now().isoformat()
        }
        
        schedules.append(new_schedule)
        save_schedules(schedules)
        
        return jsonify({
            'success': True,
            'schedule': new_schedule
        })
    except Exception as e:
        logger.error(f"Error adding schedule: {e}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/schedules/<string:schedule_id>', methods=['DELETE'])
@require_auth
def delete_schedule(schedule_id):
    """Delete a schedule"""
    try:
        schedules = load_schedules()
        initial_len = len(schedules)
        schedules = [s for s in schedules if s['id'] != schedule_id]
        
        if len(schedules) == initial_len:
            return jsonify({'error': 'Schedule not found'}), 404
            
        save_schedules(schedules)
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error deleting schedule: {e}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/schedules/<string:schedule_id>/toggle', methods=['POST'])
@require_auth
def toggle_schedule(schedule_id):
    """Enable or disable a schedule"""
    try:
        schedules = load_schedules()
        found = False
        for s in schedules:
            if s['id'] == schedule_id:
                s['enabled'] = not s.get('enabled', True)
                found = True
                break
        
        if not found:
            return jsonify({'error': 'Schedule not found'}), 404
            
        save_schedules(schedules)
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error toggling schedule: {e}")
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
