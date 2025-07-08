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

from pathlib import Path
from socketserver import ThreadingMixIn
from wsgiref.simple_server import WSGIRequestHandler, WSGIServer, make_server
import logging
import sys
from os import environ

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

    if environ.get('ENABLE_SPOOL_DIRECTORY', 'false') == 'true':
        Path.mkdir(Path(SPOOL_DIRECTORY), parents=True, exist_ok=True)
        # Cleaner
        cleaner = Cleaner()
        cleaner.daemon = True
        cleaner.start()

    try:
        aerooServices = AerooServices(spool_directory=SPOOL_DIRECTORY,
                                      soffice_restart_cmd="/usr/local/bin/officeLauncher.sh")
    except Exception as e:
        logger.error('failed to create the ApplicationServices ')
        logger.error(str(e))
        sys.exit(1)

    interfaces = {
        'convert': aerooServices.convert,
        'upload': aerooServices.upload,
        'join': aerooServices.join,
        'test': aerooServices.test,
        'log': changeLogLevel
    }

    app = ExtendedJsonRpcApplication(rpcs=interfaces)

    # WSGI requires the app to return bytes, so wrap if necessary
    def wsgi_app(environ, start_response):
        result = app(environ, start_response)
        for item in result:
            if isinstance(item, str):
                yield item.encode('utf-8')
            else:
                yield item

    try:
        httpd = make_server("0.0.0.0", 8989, wsgi_app, ThreadingWSGIServer, WSGIRequestHandler)
    except OSError as e:
        logger.error('failed to create the server ')
        if e.errno == 98:
            logger.error('Address already in use, :8989 is occupied.')
        sys.exit(1)

    logger.info('Server started')

    try:
        httpd.serve_forever()
    except KeyboardInterrupt as e:
        logger.info('Adhoc DOCS process interrupted.')
        sys.exit(0)


if __name__ == "__main__":
    main()
