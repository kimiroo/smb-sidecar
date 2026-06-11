import os
import logging

log = logging.getLogger(__name__)

__all__ = [
    'SHARE_PATH',
    'USERNAME',
    'PASSWORD',
    'SOURCE_PATH',
    'TARGET_PATH',
    'INTERVAL',
    'SMB_TIMEOUT',
    'PROC_TIMEOUT'
]

REQUIRED_ENV_VARS = {
    'SHARE_PATH',
    'USERNAME',
    'PASSWORD',
    'SOURCE_PATH',
    'TARGET_PATH'
}

# Check required env vars
missing_vars = REQUIRED_ENV_VARS - set(os.environ.keys())

if missing_vars:
    err_msg = f'Missing required environment variables: {', '.join(missing_vars)}'
    log.critical(err_msg)
    raise EnvironmentError(err_msg)

# Load env vars
SHARE_PATH = os.environ.get('SHARE_PATH')
USERNAME = os.environ.get('USERNAME')
PASSWORD = os.environ.get('PASSWORD')
SOURCE_PATH = os.environ.get('SOURCE_PATH')
TARGET_PATH = os.environ.get('TARGET_PATH')

interval_raw = os.environ.get('INTERVAL', '10')
INTERVAL = int(interval_raw) if interval_raw.isdigit() else 10

smb_timeout_raw = os.environ.get('SMB_TIMEOUT', '5')
SMB_TIMEOUT = int(smb_timeout_raw) if smb_timeout_raw.isdigit() else 5

proc_timeout_raw = os.environ.get('PROC_TIMEOUT', '10')
PROC_TIMEOUT = int(proc_timeout_raw) if proc_timeout_raw.isdigit() else 10