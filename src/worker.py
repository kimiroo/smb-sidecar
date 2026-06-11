import os
import logging
import traceback
import shutil

STATE_PATH = '/state/mtime'
TMP_FILE_PATH = '/tmp/smb_cache.tmp'

logging.getLogger('smbprotocol').setLevel(logging.WARNING)
log = logging.getLogger('worker')

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

def worker():
    import smbclient
    from smbprotocol.exceptions import LogonFailure, SMBAuthenticationError

    import util.const as const

    try:
        smbclient.register_session(
            server=const.HOSTNAME,
            username=const.USERNAME,
            password=const.PASSWORD,
            encrypt=True,
            connection_timeout=const.SMB_TIMEOUT
        )

        target_file_stat = smbclient.stat(const.SOURCE_PATH)
        target_mtime = target_file_stat.st_mtime

        if target_mtime == get_last_mtime():
            log.debug('Source file not modified. Skipping sync...')
            return

        log.info('Detected source file change.')

        log.info('Initializing...')
        if os.path.exists(TMP_FILE_PATH):
            os.remove(TMP_FILE_PATH)

        with smbclient.open_file(const.SOURCE_PATH, mode='rb') as src_f:
            with open(TMP_FILE_PATH, 'wb') as tmp_f:
                log.info('Copying source file to temp directory...')
                shutil.copyfileobj(src_f, tmp_f)

        log.info('Copying source file to target destination...')
        remote_tmp = const.TARGET_PATH + '.tmp'

        shutil.move(TMP_FILE_PATH, remote_tmp)

        if os.path.exists(const.TARGET_PATH):
            os.remove(const.TARGET_PATH)
        os.rename(remote_tmp, const.TARGET_PATH)

        log.info('Updating saved state...')
        save_last_mtime(target_mtime)

        log.info('Sync successful.')

    except (LogonFailure, SMBAuthenticationError) as e:
        log.error(f'Failed to authenticate: {e}')
    except (TimeoutError, ValueError):
        log.debug('SMB server response timed out.')
    except Exception as e:
        log.critical(f'Unexpected error: {e}')
        traceback.print_exc()