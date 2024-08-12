
import logging
from os import listdir, stat, unlink
from threading import Thread
from time import sleep, time


class Cleaner(Thread):
    """Clean old/unused files."""
    delay: int = 60
    expire: int = 1800
    spool_directory: str = '/tmp/aeroo-docs'
    spool_path: str = spool_directory + '/%s'

    def __init__(self, delay: int = 60, expire: int = 1800, spool_directory: str = '/tmp/aeroo-docs'):
        """
        Parameters
        ----------
        delay : int, optional
            Seconds between checks (default is 60)
        expire : int, optional
            seconds to consider a file obsolete (default is 1800, iqual to 30 minutes)
        spool_directory : str, optional
            directory for temp files to clean (default is '/tmp/aeroo-docs')
        """
        super(Cleaner, self).__init__()
        self.name = 'Cleaner thread'
        self.delay = delay
        self.expire = expire
        self.spool_directory = spool_directory
        self.spool_path = spool_directory + '/%s'

    def run(self):
        logger = logging.getLogger('main')
        while True:
            files = listdir(self.spool_directory)
            for fname in files:
                testfile = self.spool_path % fname
                atribs = stat(testfile)
                if int(time()) - atribs.st_mtime > self.expire:
                    unlink(testfile)
                    logger.debug(f'Cleaner: {testfile} deleted')
            sleep(self.delay)
