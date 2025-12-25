import json
from pathlib import Path
import logging

# FIXED: Import DATA_DIR for proper path [web:72]
try:
    from core import DATA_DIR, PROJECT_ROOT
except ImportError:
    # Fallback for standalone usage
    PROJECT_ROOT = Path(__file__).parent.parent
    DATA_DIR = PROJECT_ROOT / "data"

# FIXED: Use DATA_DIR instead of relative path
FLAGS_FILE = DATA_DIR / "user_flags.json"

logging.basicConfig(level=logging.INFO)


def _load_flags():
    """Load user flags from data/ folder"""
    try:
        # FIXED: Ensure data directory exists
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        
        if FLAGS_FILE.exists():
            with open(FLAGS_FILE, 'r') as f:
                flags = json.load(f)
                logging.debug(f"User flags loaded from {FLAGS_FILE}: {len(flags)} users")
                return flags
    except Exception as e:
        logging.error(f"Error loading user flags: {str(e)}")
    return {}


def _save_flags(flags):
    """Save user flags to data/ folder"""
    try:
        # FIXED: Ensure data directory exists
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        
        with open(FLAGS_FILE, 'w') as f:
            json.dump(flags, f, indent=2)
        logging.debug(f"User flags saved to {FLAGS_FILE}: {len(flags)} users")
    except Exception as e:
        logging.error(f"Error saving user flags: {str(e)}")


def set_must_reset(user_id, value=True):
    """Set must_reset flag for user"""
    flags = _load_flags()
    flags[str(user_id)] = {'must_reset': bool(value)}
    _save_flags(flags)
    logging.info(f"Set must_reset={value} for user {user_id}")


def clear_must_reset(user_id):
    """Clear must_reset flag for user"""
    flags = _load_flags()
    if str(user_id) in flags:
        flags[str(user_id)]['must_reset'] = False
        _save_flags(flags)
        logging.info(f"Cleared must_reset for user {user_id}")


def must_reset(user_id):
    """Check if user must reset password"""
    flags = _load_flags()
    result = flags.get(str(user_id), {}).get('must_reset', False)
    logging.debug(f"must_reset check for user {user_id}: {result}")
    return result
