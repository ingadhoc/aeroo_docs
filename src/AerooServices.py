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
import subprocess
from time import sleep, time
from os import path, rename
import uuid
import zipfile
from CallWithTimeout import ExecutorWithTimeout, TimeoutExeption
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
        self.spool_path = spool_directory + "/%s"
        self.soffice_restart_cmd = soffice_restart_cmd

    def _init_conn(self):
        try:
            return StarOfficeClient(ooo_restart_cmd=self.soffice_restart_cmd)
        except StarOfficeClientException as e:
            logger = logging.getLogger('main')
            logger.warning("Failed to initiate LibreOffice connection.")
            return None

    def _md5(self, data: str) -> str:
        return md5(data.encode()).hexdigest()

    def _conn_healthy(self):
        logger = logging.getLogger('main')
        attempt = 0
        star_office_client = None
        while star_office_client is None and attempt < 7:
            attempt += 1
            star_office_client = self._init_conn()
            if star_office_client is not None:
                logger.info("LibreOffice connection initialized.")
                return star_office_client
            sleep(10)

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
        call_ref = str(uuid.uuid4()).replace("-", "")[:6]
        logger = logging.getLogger('main')
        logger.debug('%s Upload identifier: %s from %s' % (call_ref, identifier, client_id))
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
                logger.debug('%s  assigning new identifier %s' % (call_ref, new_ident))
                # check if there is any other such files
                identifier = not path.isfile(self.spool_path % '_'+fname) \
                    and not path.isfile(self.spool_path % fname) \
                    and new_ident or False

            fname = fname or self._md5(str(identifier))
            with open(self.spool_path % '_'+fname, "a") as tmpfile:
                tmpfile.write(data)

            logger.debug("%s  chunk finished %s" % (call_ref, self._chktime(start_time)))
            if is_last:
                rename(self.spool_path % '_'+fname, self.spool_path % fname)
                logger.debug("%s  file finished" % call_ref)

            return {'identifier': identifier}

        except (AccessException, NoidentException, NodataException) as e:
            raise e
        except:
            import sys
            import traceback
            exceptionType, exceptionValue, exceptionTraceback = sys.exc_info()
            traceback.print_exception(
                exceptionType, exceptionValue, exceptionTraceback, limit=2, file=sys.stdout)

    def convert(self, data=False, identifier=False, in_mime=False, out_mime=False, username=None, password=None, client_id='Unknown'):
        try:
            rta = ExecutorWithTimeout().callWithTimeout(
                100,
                self._convert,
                (data, identifier, in_mime, out_mime, username, password, client_id)
            )
            return rta
        except TimeoutExeption as toe:
            self._restart_ooo()
            raise Exception('The file cannot be processed')
        except Exception as e:
            raise e

    def _convert(self, data=False, identifier=False, in_mime=False, out_mime=False, username=None, password=None, client_id='Unknown'):
        call_ref = str(uuid.uuid4()).replace("-", "")[:6]
        logger = logging.getLogger('main')
        start_time = time()
        logger.debug('%s Convert File Solicitation from %s at %s: ' % (call_ref, client_id, datetime.now()))

        if data is not False:
            data = base64.b64decode(data)
            logger.debug('%s Openning file from %s : ' % (call_ref, client_id))
        elif identifier is not False:
            logger.debug('%s Openning identifier %s from %s :' % (call_ref, identifier, client_id))
            data = self._readFile(identifier)
        else:
            raise NoidentException('Wrong or no identifier.')

        logger.debug("%s  read file %s len %s" % (call_ref, self._chktime(start_time), convert_size(len(data))))

        # Avoid to handle files with too many images.
        inzip = zipfile.ZipFile(io.BytesIO(data), "r")
        if len(inzip.namelist()) > 2175:
            raise Exception('File with too many images')
        inzip = None

        star_office_client = self._conn_healthy()
        if star_office_client == None:
            raise Exception('Client Not available')

        logger.debug("%s  connection test ok %s" % (call_ref, self._chktime(start_time)))
        infilter = filters.get(in_mime, False)
        outfilter = filters.get(out_mime, False)

        star_office_client.putDocument(
            data, filter_name=infilter, read_only=True)

        logger.debug("%s  upload document to office %s" %
                     (call_ref, self._chktime(start_time)))

        try:
            conv_data = star_office_client.saveByStream(
                filter_name=outfilter)
            logger.debug("%s  download converted document %s" %
                         (call_ref, self._chktime(start_time)))
        except Exception as e:
            logger.debug("%s  conversion failed %s Exception: %s" %
                         (call_ref, self._chktime(start_time), str(e)))
            star_office_client.closeDocument()
            logger.debug("%s  emergency close document %s" %
                         (call_ref, self._chktime(start_time)))
            raise e
        else:
            star_office_client.closeDocument()
            logger.debug("%s  close document %s" % (call_ref, self._chktime(start_time)))

        return base64.b64encode(conv_data).decode('utf8')

    def join(self, idents, in_mime=False, out_mime=False, username=None, password=None, client_id='Unknown'):
        call_ref = str(uuid.uuid4()).replace("-", "")[:6]
        logger = logging.getLogger('main')
        logger.debug('%s Join %s identifiers: %s' %
                     (call_ref, str(len(idents)), str(idents)))

        start_time = time()
        ident = idents.pop(0)
        data = self._readFile(ident)
        logger.debug("%s  read first file %s" % (call_ref, self._chktime(start_time)))

        star_office_client = self._conn_healthy()
        logger.debug("%s  connection test ok %s" % (call_ref, self._chktime(start_time)))

        try:
            infilter = filters.get(in_mime, False) or 'writer8'
            outfilter = filters.get(out_mime, False)
            star_office_client.putDocument(
                data, filter_name=infilter, read_only=True)
            logger.debug("%s  upload first document to office %s" %
                         (call_ref, self._chktime(start_time)))
            star_office_client.appendDocuments(
                self._readFiles(idents), filter_name=infilter)
            result_data = star_office_client.saveByStream(outfilter)
        except Exception as e:
            logger.debug("%s  conversion failed %s Exception: %s" %
                         (call_ref, self._chktime(start_time), str(e)))
            star_office_client.closeDocument()
            logger.debug("%s  emergency close document %s" %
                         (call_ref, self._chktime(start_time)))
            raise e
        else:
            star_office_client.closeDocument()
            logger.debug("%s  close document %s" % (call_ref, self._chktime(start_time)))

        logger.debug("%s  join finished %s" % (call_ref, self._chktime(start_time)))
        return base64.b64encode(result_data).decode('utf8')

    def test(self, client_id=''):
        localPath = Path(__file__).resolve().absolute().with_name('test.odt')
        with open(localPath, "rb") as tmpfile:
            data = base64.b64encode(tmpfile.read()).decode('utf-8')

        result = self.convert(data, in_mime='odt', out_mime='pdf')[:4]
        if 'JVBE' == result:  # b'%PDF' Check for magick words
            return {'status': 'ok', 'dig': result[:128]}

        raise Exception('Convertion failed')

    def _restart_ooo(self):
        logger = logging.getLogger('main')
        if not self.soffice_restart_cmd:
            logger.warning(
                'No LibreOffice/OpenOffice restart script configured')
            return False
        logger.info(
            'Restarting LibreOffice/OpenOffice background process')
        try:
            logger.info('Executing restart script "%s"' %
                        self.soffice_restart_cmd)
            subprocess.Popen(self.soffice_restart_cmd, start_new_session=True)
            sleep(4)  # Let some time for LibO/OOO to be fully started
        except OSError as e:
            logger.error(
                'Failed to execute the restart script. OS error: %s' % e)
        except Exception as e:
            logger.error(
                'Failed to execute the restart script. General error: %s' % e)
        return True
