import os
import re
import logging
import subprocess
import datetime
import shutil

STATE_PATH = '/state/mtime'
TMP_FILE_PATH = '/tmp/smb_cache.tmp'

logging.getLogger('smbprotocol').setLevel(logging.WARNING)
log = logging.getLogger('worker')

import util.const as const

def get_last_mtime():
    if not os.path.exists(STATE_PATH):
        return 0.0

    try:
        with open(STATE_PATH, 'r', encoding='utf-8') as f:
            raw_mtime = f.read().strip()
            return float(raw_mtime)
    except (ValueError, TypeError):
        return 0.0

def save_last_mtime(mtime):
    with open(STATE_PATH, 'w', encoding='utf-8') as f:
        f.write(str(mtime))

def get_remote_mtime_via_cli():
    cmd = [
        "smbclient", const.SHARE_PATH,
        f"-U={const.USERNAME}%{const.PASSWORD}",
        "-c", f"allinfo {const.SOURCE_PATH}"
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            timeout=const.SMB_TIMEOUT
        )

        match = re.search(r"write_time:\s+(.+)", result.stdout)
        if match:
            raw_time_str = match.group(1).strip()
            clean_time_str = " ".join(raw_time_str.split()[:5]) # "Wed Jun 11 14:15:00 2026"
            dt = datetime.datetime.strptime(clean_time_str, "%a %b %d %H:%M:%S %Y")
            return dt.timestamp()

    except subprocess.CalledProcessError as e:
        log.debug(f"smbclient allinfo failed. stderr: {e.stderr.strip()}")
    except Exception as e:
        log.debug(f"Failed to fetch remote mtime via CLI: {e}")
    return None

def worker():
    target_mtime = get_remote_mtime_via_cli()

    if target_mtime is None:
        log.debug('Could not resolve remote file status. Skipping this cycle...')
        return

    if target_mtime == get_last_mtime():
        log.debug('Source file not modified. Skipping sync...')
        return

    log.info('Detected source file change.')
    if os.path.exists(TMP_FILE_PATH):
        os.remove(TMP_FILE_PATH)

    download_cmd = [
        "smbclient", const.SHARE_PATH,
        f"-U={const.USERNAME}%{const.PASSWORD}",
        "-c", f"get {const.SOURCE_PATH} {TMP_FILE_PATH}"
    ]

    try:
        log.info('Downloading source file via smbclient CLI...')
        subprocess.run(
            download_cmd,
            capture_output=True,
            text=True,
            check=True,
            timeout=const.SMB_TIMEOUT
        )

        log.info('Copying source file to target destination...')
        remote_tmp = const.TARGET_PATH + '.tmp'
        shutil.move(TMP_FILE_PATH, remote_tmp)

        if os.path.exists(const.TARGET_PATH):
            os.remove(const.TARGET_PATH)
        os.rename(remote_tmp, const.TARGET_PATH)

        log.info('Updating saved state...')
        save_last_mtime(target_mtime)

        log.info('Sync successful.')

    except subprocess.CalledProcessError as e:
        log.error(f'CLI download failed: {e.stderr.strip()}')
    except Exception as e:
        log.critical(f'Unexpected error: {e}')