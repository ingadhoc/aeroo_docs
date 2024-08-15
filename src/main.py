################################################################################
#
# Copyright (c) 2009-2014 Alistek ( http://www.alistek.com )
#               All Rights Reserved.
#               General contacts <info@alistek.com>
# Copyleft (ↄ) 2024 Andrés Zacchino <az@adhoc.com.ar>
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 3
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
################################################################################

import os
from pathlib import Path
from socketserver import ThreadingMixIn
from wsgiref.simple_server import WSGIRequestHandler, WSGIServer, make_server
import logging
import sys
from os import mkdir

from AerooServices import AerooServices
from Cleaner import Cleaner
from ExtendedJsonRpcApplication import ExtendedJsonRpcApplication

SPOOL_DIRECTORY = '/tmp/aeroo-docs'


def changeLogLevel(verbose: bool, client_id: str):
    logging.getLogger('main').setLevel(
        logging.DEBUG if verbose else logging.INFO)
    return {'rta': 'changed'}


class ThreadingWSGIServer(ThreadingMixIn, WSGIServer):
    pass


def main():
    logger = logging.getLogger('main')
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.DEBUG)

    if os.environ.get('ENABLE_SPOOL_DIRECTORY', 'false') == 'true':
        try:
            if not Path(SPOOL_DIRECTORY).is_dir():
                mkdir(SPOOL_DIRECTORY)
        finally:
            pass
        # Cleaner
        cleaner = Cleaner()
        cleaner.setDaemon(True)
        cleaner.start()

    try:
        aerooServices = AerooServices(spool_directory=SPOOL_DIRECTORY)
    except Exception as e:
        logger.error('failed to create the ApplicationServices ')
        logger.error(str(e))
        return e

    interfaces = {
        'convert': aerooServices.convert,
        'upload': aerooServices.upload,
        'join': aerooServices.join,
        'test': aerooServices.test,
        'log': changeLogLevel
    }

    app = ExtendedJsonRpcApplication(rpcs=interfaces)
    try:
        httpd = make_server("0.0.0.0", 8989, app, ThreadingWSGIServer, WSGIRequestHandler)
    except OSError as e:
        logger.error('failed to create the server ')
        if e.errno == 98:
            logger.error('Address allready in use, :8989 is occupied.')
        sys.exit()

    logger.info('Server started')

    try:
        httpd.serve_forever()
    except KeyboardInterrupt as e:
        logger.info('Adhoc DOCS process interrupted.')
        sys.exit()


if __name__ == "__main__":
    main()
