#!/usr/bin/env python
#
# inspired by PyODConverter (Python OpenDocument Converter) v1.0.0 - 2008-05-05
#
# This script converts a document from one office format to another by
# connecting to an OpenOffice.org instance via Python-UNO bridge.
#
# Copyright (C) 2009 Alistek Ltd. (www.alistek.com)
# Licensed under the GNU LGPL v2.1 - http://www.gnu.org/licenses/lgpl-2.1.html
# - or any later version.
# Copyleft (ↄ) 2024 Andrés Zacchino <az@adhoc.com.ar>
#
import uno
from com.sun.star.text import ControlCharacter
from com.sun.star.document import MacroExecMode
from com.sun.star.document import UpdateDocMode
from com.sun.star.io import XOutputStream
from com.sun.star.lang import IllegalArgumentException, DisposedException
from com.sun.star.beans import UnknownPropertyException
from com.sun.star.connection import NoConnectException, ConnectionSetupException
from com.sun.star.beans import PropertyValue

import unohelper
from io import BytesIO
import logging
import subprocess
import time
import traceback
import sys
from os.path import abspath
DEFAULT_OPENOFFICE_PORT = 2002
RESOLVESTR = "uno:socket,host=%s,port=%s;urp;StarOffice.ComponentContext"

################## For CSV documents #######################
# Field Separator (1), Text Delimiter (2), Character Set (3), Number of First Line (4)
CSVFilterOptions = "59,34,76,1"
# ASCII code of field separator
# ASCII code of text delimiter
# character set, use 0 for "system character set", 76 seems to be UTF-8
# number of first line (1-based)
# Cell format codes for the different columns (optional)
############################################################


# from com.sun.star.document.UpdateDocMode import QUIET_UPDATE
# from com.sun.star.document.MacroExecMode import NEVER_EXECUTE
# from com.sun.star.style.BreakType import PAGE_AFTER, PAGE_BEFORE, PAGE_BOTH
# from com.sun.star.text.ControlCharacter import PARAGRAPH_BREAK, APPEND_PARAGRAPH

SECTIONMAXLEVEL = 10  # Just to make sure we do not go into endless loop


class StarOfficeClientException(Exception):

    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message


class OutputStreamWrapper(unohelper.Base, XOutputStream):
    """ Minimal Implementation of XOutputStream """

    def __init__(self, debug=True):
        self.debug = debug
        self.data = BytesIO()
        self.position = 0
        if self.debug:
            sys.stderr.write("__init__ OutputStreamWrapper.\n")

    def writeBytes(self, bytes):
        if self.debug:
            sys.stderr.write("writeBytes %i bytes.\n" % len(bytes.value))
        self.data.write(bytes.value)
        self.position += len(bytes.value)

    def close(self):
        if self.debug:
            sys.stderr.write(
                "Closing output. %i bytes written.\n" % self.position)
        self.data.close()

    def flush(self):
        if self.debug:
            sys.stderr.write("Flushing output.\n")
        pass

    def closeOutput(self):
        if self.debug:
            sys.stderr.write("Closing output.\n")
        pass


class StarOfficeClient:

    def __init__(self, host='localhost', port=DEFAULT_OPENOFFICE_PORT, ooo_restart_cmd=None):
        self._host = host
        self._port = port
        self.logger = logging.getLogger('main')
        self._ooo_restart_cmd = ooo_restart_cmd
        self.localContext = uno.getComponentContext()
        self.serviceManager = self.localContext.ServiceManager
        resolvervector = "com.sun.star.bridge.UnoUrlResolver"
        self._resolver = self.serviceManager.createInstanceWithContext(
            resolvervector, self.localContext)
        try:
            self._connectOffice()
        except IllegalArgumentException as exception:
            raise StarOfficeClientException(
                "The url is invalid (%s)" % exception)
        except NoConnectException as exception:
            if self._restart_ooo():
                # We try again once
                try:
                    self._connectOffice()
                except NoConnectException as exception:
                    raise StarOfficeClientException(
                        "Failed to connect to OpenOffice.org on host %s, port %s. %s" % (host, port, exception))
            else:
                raise StarOfficeClientException(
                    "Failed to connect to OpenOffice.org on host %s, port %s. %s" % (host, port, exception))

        except ConnectionSetupException as exception:
            raise StarOfficeClientException(
                "Not possible to accept on a local resource (%s)" % exception)

    def putDocument(self, data, filter_name=False, read_only=False):
        """
        Uploads document to office service
        """
        try:
            if not hasattr(self, 'desktop'):
                self._createDesktop()
            elif self.desktop is None:
                self._createDesktop()
        except UnknownPropertyException:
            self._connectOffice()
            self._createDesktop()
        inputStream = self._initStream(data)
        properties = {'InputStream': inputStream}
        properties.update({'Hidden': True})
        properties.update({'UpdateDocMode': UpdateDocMode.QUIET_UPDATE})
        properties.update({'ReadOnly': read_only})
        properties.update({'MacroExecutionMode': MacroExecMode.NEVER_EXECUTE})

        # TODO Minor performance improvement by supplying MediaType property
        # properties.update({'MediaType':'application/vnd.oasis.opendocument.text'})

        if filter_name:
            properties.update({'FilterName': filter_name})
        props = self._toProperties(**properties)
        try:
            self.document = self.desktop.loadComponentFromURL(
                'private:stream', '_blank', 0, props)
        except DisposedException as e:
            #   When office unexpectedly crashed or has been restarted, we know
            # nothing about it, that is why we need to create new desktop or
            # even try to completely reconnect to new office socket. Then give
            # it another try.
            self._createDesktop()
            self.putDocument(data, filter_name=filter_name,
                             read_only=read_only)
        except Exception as e:
            exceptionType, exceptionValue, exceptionTraceback = sys.exc_info()
            traceback.print_exception(exceptionType, exceptionValue,
                                      exceptionTraceback, limit=2, file=sys.stdout)
        inputStream.closeInput()

    def closeDocument(self):
        if hasattr(self, 'document'):
            if self.document is not None:
                self.document.close(True)
                del self.document

    def saveByStream(self, filter_name=None):
        """
        Downloads document from office service
        """
        self._updateDocument()
        outputStream = OutputStreamWrapper(False)
        properties = {"OutputStream": outputStream}
        properties.update({"FilterName": filter_name})
        if filter_name == 'Text - txt - csv (StarCalc)':
            properties.update({"FilterOptions": CSVFilterOptions})
        props = self._toProperties(**properties)
        try:
            # url = uno.systemPathToFileUrl(path) #when storing to filesystem
            self.document.storeToURL('private:stream', props)
        except Exception as exception:
            exceptionType, exceptionValue, exceptionTraceback = sys.exc_info()
            traceback.print_exception(exceptionType, exceptionValue,
                                      exceptionTraceback, limit=2, file=sys.stdout)
        openDocumentBytes = outputStream.data.getvalue()
        outputStream.close()
        return openDocumentBytes

    def appendDocuments(self, docs_iter, filter_name=False, preserve_styles=True):
        # Get first document list of styles
        stylefamilies = self.document.StyleFamilies
        pagestyles = stylefamilies.getByName('PageStyles')
        defaultpagetyle = pagestyles.getElementNames()[0]
        # Seemingly not needed
        # parastyles = stylefamilies.getByName('ParagraphStyles')
        # defaultparatyle = parastyles.getElementNames()[0]

        text = self.document.Text
        cursor = text.createTextCursor()
        cursor.gotoStart(False)

        # Get first page styles
        cursor.gotoStartOfParagraph(False)
        cursor.gotoEndOfParagraph(True)

        pagestyle = cursor.PageDescName or defaultpagetyle

        for doc in docs_iter:
            subStream = self._initStream(doc)
            properties = {'InputStream': subStream}
            properties.update({'FilterName': filter_name})
            props = self._toProperties(**properties)
            try:
                cursor.gotoEnd(False)
                cur_sect = cursor.TextSection
                if cur_sect is not None:
                    # drilldown to bottom
                    lowersect = cur_sect
                    parent_sect = True
                    level = 0
                    while parent_sect and level < SECTIONMAXLEVEL:
                        parent_sect = lowersect.getParentSection()
                        if parent_sect:
                            lowersect = parent_sect
                            level += 1
                    # TODO Implement check if section is not anchored to page gloablly...
                    # cur_pos = ancestor.AnchorType
                    paravector = 'com.sun.star.text.Paragraph'
                    newpara = self.document.createInstance(paravector)
                    text.insertTextContentAfter(newpara, lowersect)
                else:
                    text.insertControlCharacter(
                        cursor, ControlCharacter.APPEND_PARAGRAPH, 0)
                cursor.gotoEnd(False)
                cursor.gotoStartOfParagraph(False)
                cursor.gotoEndOfParagraph(True)
                cursor.PageDescName = pagestyle
                cursor.PageNumberOffset = 1
                # Seemingly not needed
                # cursor.ParaStyleName = parastyle
                self.document.Text.getEnd().insertDocumentFromURL('private:stream', props)

            except Exception as e:
                print("Error inserting file %s bytes on the OpenOffice document: %s" % (
                    len(doc), e))
                raise e
        self._updateDocument()

    def _connectOffice(self):
        self._context = self._resolver.resolve(
            RESOLVESTR % (self._host, self._port))

    def _createDesktop(self):
        try:
            smanager = self._context.ServiceManager
            self.desktop = smanager.createInstanceWithContext(
                "com.sun.star.frame.Desktop", self._context)
        except UnknownPropertyException as e:
            self._connectOffice()
            self._createDesktop()

    def _updateDocument(self):
        try:
            self.document.updateLinks()
        except AttributeError:
            # if document doesn't support XLinkUpdate interface
            pass
        try:
            self.document.refresh()
            indexes = self.document.getDocumentIndexes()
        except AttributeError:
            # ods document does not support refresh
            pass
        else:
            for inc in range(0, indexes.getCount()):
                indexes.getByIndex(inc).update()

    def _initStream(self, data):
        streamvector = "com.sun.star.io.SequenceInputStream"
        subStream = self.serviceManager.createInstanceWithContext(
            streamvector, self.localContext)
        subStream.initialize((uno.ByteSequence(data),))
        return subStream

    def _toFileUrl(self, path):
        return uno.systemPathToFileUrl(abspath(path))

    def _toProperties(self, **args):
        props = []
        for key in args:
            prop = PropertyValue()
            prop.Name = key
            prop.Value = args[key]
            props.append(prop)
        return tuple(props)

    def _restart_ooo(self):
        if not self._ooo_restart_cmd:
            self.logger.warning(
                'No LibreOffice/OpenOffice restart script configured')
            return False
        self.logger.info(
            'Restarting LibreOffice/OpenOffice background process')
        try:
            self.logger.info('Executing restart script "%s"' %
                             self._ooo_restart_cmd)
            retcode = subprocess.call(self._ooo_restart_cmd, shell=True)
            if retcode == 0:
                self.logger.warning('Restart successfull')
                time.sleep(4)  # Let some time for LibO/OOO to be fully started
            else:
                self.logger.error(
                    'Restart script failed with return code %d' % retcode)
        except OSError as e:
            self.logger.error(
                'Failed to execute the restart script. OS error: %s' % e)
        return True

    # def convertByPath(self, inputFile, outputFile):
    #     inputUrl = self._toFileUrl(inputFile)
    #     outputUrl = self._toFileUrl(outputFile)
    #     props = self._toProperties(Hidden=True)
    #     document = self.desktop.loadComponentFromURL(inputUrl, "_blank", 8, props)
    #     try:
    #         document.refresh()
    #     except AttributeError:
    #         pass
    #     props = self._toProperties(FilterName="writer_pdf_Export")
    #     try:
    #         document.storeToURL(outputUrl, props)
    #     finally:
    #         document.close(True)

    # def insertSubreports(self, oo_subreports):
    #     """
    #     Inserts the given file into the current document.
    #     The file contents will replace the placeholder text.
    #     """
    #     import os

    #     for subreport in oo_subreports:
    #         fd = file(subreport, 'rb')
    #         placeholder_text = "<insert_doc('%s')>" % subreport
    #         subdata = fd.read()
    #         subStream = self._initStream(subdata)
    #         search = self.document.createSearchDescriptor()
    #         search.SearchString = placeholder_text
    #         found = self.document.findFirst( search )
    #         #while found:
    #         properties = {'InputStream':subStream}
    #         properties.update({'FilterName':"writer8"})
    #         props = self._toProperties(**properties)
    #         try:
    #             found.insertDocumentFromURL('private:stream', props)
    #         except Exception as ex:
    #             print("Error inserting file %s on the OpenOffice document: %s" % (subreport, ex))
    #             exceptionType, exceptionValue, exceptionTraceback = sys.exc_info()
    #             traceback.print_exception(exceptionType, exceptionValue,
    #                             exceptionTraceback, limit=2, file=sys.stdout)
    #         #found = self.document.findNext(found, search)

    #         os.unlink(subreport)
