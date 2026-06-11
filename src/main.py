import time
import logging
import multiprocessing

logging.basicConfig(
    format='%(asctime)s [%(levelname)s] [%(name)s] %(message)s',
    level='INFO',
    datefmt='%Y-%m-%d %H:%M:%S',
)
log = logging.getLogger('main')

from worker import worker
import util.const as const


def main():
    while True:
        log.debug('Starting sync worker...')

        p = multiprocessing.Process(target=worker)
        p.start()

        # Monitor the process for up to 10 seconds
        p.join(timeout=const.PROC_TIMEOUT)

        if p.is_alive():
            log.warning('Sync task hung or exceeded timeout limit! Force killing worker...')
            p.terminate()
            p.join()

        log.debug('Sleeping for 10 seconds before next cycle...')
        time.sleep(const.INTERVAL)

if __name__ == '__main__':
    main()