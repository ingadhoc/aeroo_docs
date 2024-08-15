################################################################################
#
# Copyright (c) 2009-2014 Alistek ( http://www.alistek.com ) All Rights Reserved.
#                    General contacts <info@alistek.com>
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

import base64
from datetime import datetime
from hashlib import md5
import io
import logging
from pathlib import Path
from random import randint
from time import sleep, time
from os import path, rename
import zipfile
from StarOfficeClient import StarOfficeClient, StarOfficeClientException
from utils import convert_size

MAXINT = 9223372036854775807

filters = {
    'pdf': 'writer_pdf_Export',   # PDF - Portable Document Format
    'odt': 'writer8',  # ODF Text Document
    'ods': 'calc8',   # ODF Spreadsheet
    'doc': 'MS Word 97',  # Microsoft Word 97/2000/XP
    'xls': 'MS Excel 97',  # Microsoft Excel 97/2000/XP
    'csv': 'Text - txt - csv (StarCalc)',  # Text CSV
}


class NoidentException(Exception):
    pass


class NodataException(Exception):
    pass


class NoOfficeConnection(Exception):
    pass


class AccessException(Exception):
    pass


class AerooServices():

    spool_path: str = "/tmp/aeroo-docs/%s"
    star_office_client = None
    soffice_restart_cmd = None

    def __init__(self, spool_directory: str, soffice_restart_cmd=None):
        self._init_conn()
        self.spool_path = spool_directory + "/%s"
        self.soffice_restart_cmd = soffice_restart_cmd

    def _init_conn(self) -> None:
        logger = logging.getLogger('main')
        try:
            self.star_office_client = StarOfficeClient(ooo_restart_cmd=self.soffice_restart_cmd)
        except StarOfficeClientException as e:
            self.star_office_client = None
            logger.warning("Failed to initiate LibreOffice connection.")

    def _md5(self, data: str) -> str:
        return md5(data.encode()).hexdigest()

    def _conn_healthy(self) -> bool:

        if self.star_office_client is not None:
            return True

        logger = logging.getLogger('main')
        attempt = 0
        while self.star_office_client is None and attempt < 3:
            attempt += 1
            self._init_conn()
            if self.star_office_client is not None:
                return True
            sleep(3)

        message = 'Failed to initiate connection to LibreOffice three times in a row.'
        logger.warning(message)
        raise NoOfficeConnection(message)

    def _chktime(self, start_time: float):
        return '%s s' % str(round(time()-start_time, 6))

    def _readFile(self, ident):
        with open(self.spool_path % self._md5(str(ident)), "r") as tmpfile:
            data = tmpfile.read()
        return base64.b64decode(data)

    def _readFiles(self, idents):
        logger = logging.getLogger('main')
        for ident in idents:
            start_time = time()
            data = self._readFile(ident)
            logger.debug("    read next file: %s +%s" %
                         (ident, self._chktime(start_time)))
            yield data

    def upload(self, data=False, is_last=False, identifier=False, username=None, password=None, client_id='Unknown'):
        logger = logging.getLogger('main')
        logger.debug('Upload identifier: %s from %s' % (identifier, client_id))
        try:
            start_time = time()
            # NOTE:md5 conversion on file operations to prevent path injection attack
            if identifier and not path.isfile(self.spool_path % '_' + self._md5(str(identifier))):
                raise NoidentException('Wrong or no identifier.')
            elif data is False:
                raise NodataException('No data to be converted.')

            fname = ''
            # generate random identifier
            while not identifier:
                new_ident = randint(1, MAXINT)
                fname = self._md5(str(new_ident))
                logger.debug('  assigning new identifier %s' % new_ident)
                # check if there is any other such files
                identifier = not path.isfile(self.spool_path % '_'+fname) \
                    and not path.isfile(self.spool_path % fname) \
                    and new_ident or False

            fname = fname or self._md5(str(identifier))
            with open(self.spool_path % '_'+fname, "a") as tmpfile:
                tmpfile.write(data)

            logger.debug("  chunk finished %s" % self._chktime(start_time))
            if is_last:
                rename(self.spool_path % '_'+fname, self.spool_path % fname)
                logger.debug("  file finished")

            return {'identifier': identifier}

        except AccessException as e:
            raise e
        except NoidentException as e:
            raise e
        except NodataException as e:
            raise e
        except:
            import sys
            import traceback
            exceptionType, exceptionValue, exceptionTraceback = sys.exc_info()
            traceback.print_exception(
                exceptionType, exceptionValue, exceptionTraceback, limit=2, file=sys.stdout)

    def convert(self, data=False, identifier=False, in_mime=False, out_mime=False, username=None, password=None, client_id='Unknown'):
        logger = logging.getLogger('main')
        start_time = time()
        logger.debug('Convert File Solicitation from %s at %s: ' % (client_id, datetime.now()))

        if data is not False:
            data = base64.b64decode(data)
            logger.debug('Openning file from %s : ' % client_id)
        elif identifier is not False:
            logger.debug('Openning identifier %s from %s :' % (identifier, client_id))
            data = self._readFile(identifier)
        else:
            raise NoidentException('Wrong or no identifier.')

        logger.debug("  read file %s len %s" % (self._chktime(start_time), convert_size(len(data))))

        # Avoid to handle files with too many images.
        inzip = zipfile.ZipFile(io.BytesIO(data), "r")
        if len(inzip.namelist()) > 2175:
            raise Exception('File with too many images')
        inzip = None

        self._conn_healthy()
        logger.debug("  connection test ok %s" % self._chktime(start_time))
        infilter = filters.get(in_mime, False)
        outfilter = filters.get(out_mime, False)

        self.star_office_client.putDocument(
            data, filter_name=infilter, read_only=True)
        logger.debug("  upload document to office %s" %
                     self._chktime(start_time))

        try:
            conv_data = self.star_office_client.saveByStream(
                filter_name=outfilter)
            logger.debug("  download converted document %s" %
                         self._chktime(start_time))
        except Exception as e:
            logger.debug("  conversion failed %s Exception: %s" %
                         (self._chktime(start_time), str(e)))
            self.star_office_client.closeDocument()
            logger.debug("  emergency close document %s" %
                         self._chktime(start_time))
            raise e
        else:
            self.star_office_client.closeDocument()
            logger.debug("  close document %s" % self._chktime(start_time))

        return base64.b64encode(conv_data).decode('utf8')

    def join(self, idents, in_mime=False, out_mime=False, username=None, password=None, client_id='Unknown'):
        logger = logging.getLogger('main')
        logger.debug('Join %s identifiers: %s' %
                     (str(len(idents)), str(idents)))

        start_time = time()
        ident = idents.pop(0)
        data = self._readFile(ident)
        logger.debug("  read first file %s" % self._chktime(start_time))

        self._conn_healthy()
        logger.debug("  connection test ok %s" % self._chktime(start_time))

        try:
            infilter = filters.get(in_mime, False) or 'writer8'
            outfilter = filters.get(out_mime, False)
            self.star_office_client.putDocument(
                data, filter_name=infilter, read_only=True)
            logger.debug("  upload first document to office %s" %
                         self._chktime(start_time))
            self.star_office_client.appendDocuments(
                self._readFiles(idents), filter_name=infilter)
            result_data = self.star_office_client.saveByStream(outfilter)
        except Exception as e:
            logger.debug("  conversion failed %s Exception: %s" %
                         (self._chktime(start_time), str(e)))
            self.star_office_client.closeDocument()
            logger.debug("  emergency close document %s" %
                         self._chktime(start_time))
            raise e
        else:
            self.star_office_client.closeDocument()
            logger.debug("  close document %s" % self._chktime(start_time))

        logger.debug("  join finished %s" % self._chktime(start_time))
        return base64.b64encode(result_data).decode('utf8')

    def test(self):
        localPath = Path(__file__).resolve().absolute().with_name('test.odt')
        with open(localPath, "rb") as tmpfile:
            data = base64.b64encode(tmpfile.read()).decode('utf-8')

        result = self.convert(data, in_mime='odt', out_mime='pdf')[:4]
        if 'JVBE' == result:  # b'%PDF' Check for magick words
            return {'status': 'ok', 'dig': result[:128]}

        raise Exception('Convertion failed')
