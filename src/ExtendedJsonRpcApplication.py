import json
from urllib.parse import parse_qs
from xmlrpc.client import PARSE_ERROR
from jsonrpc2 import JsonRpcApplication, errors, logger, GENERIC_APPLICATION_ERROR


class ExtendedJsonRpcApplication(JsonRpcApplication):

    def __call__(self, environ, start_response):
        logger.debug("jsonrpc")
        logger.debug("check method")

        # Allow GET Methods
        if environ['REQUEST_METHOD'] == 'GET':
            query_string = environ['QUERY_STRING']
            parsed_qs = parse_qs(query_string)

            data: dict = {
                'method': parsed_qs.get('method', [None])[0],
                'params': json.loads(parsed_qs.get('params', ["{}"])[0]),
                'id': parsed_qs.get('id', [1])[0],
                'jsonrpc': parsed_qs.get('jsonrpc', ["2.0"])[0],
            }
            resdata = self.rpc(data)

            if not resdata:
                return []

            if 'error' in resdata:
                if resdata['error'].get('code', GENERIC_APPLICATION_ERROR) == GENERIC_APPLICATION_ERROR:
                    start_response('500 Internal Server Error', [('Content-Type', 'application/json')])
                    return [json.dumps(resdata).encode('utf-8')]

            start_response('200 OK', [('Content-Type', 'application/json')])
            return [json.dumps(resdata).encode('utf-8')]

        # POST: Add automaticaly missing params
        if environ['REQUEST_METHOD'] != "POST":
            start_response('405 Method Not Allowed',
                           [('Content-type', 'text/plain')])
            return ["405 Method Not Allowed"]

        logger.debug("check content-type")
        if environ['CONTENT_TYPE'].split(';', 1)[0] not in ('application/json', 'application/json-rpc'):
            start_response('400 Bad Request',
                           [('Content-type', 'text/plain')])
            return ["Content-type must by application/json"]

        content_length = -1
        if "CONTENT_LENGTH" in environ:
            content_length = int(environ["CONTENT_LENGTH"])
        try:
            body = environ['wsgi.input'].read(content_length)
            body = body.decode('utf-8')
            data: dict = json.loads(body)
            if not data['params']:
                data['params'] = {}
            if not 'client_id' in data['params']:
                data['params']['client_id'] = 'unknown - %s' % environ['REMOTE_ADDR']

            resdata = self.rpc(data)
            logger.debug("response %s" % json.dumps(resdata))
        except ValueError as e:
            resdata = {
                'jsonrpc': '2.0',
                'id': None,
                'error': {
                    'code': PARSE_ERROR,
                    'message': errors[PARSE_ERROR]
                }
            }

        start_response('200 OK',
                       [('Content-type', 'application/json')])

        if resdata:
            return [json.dumps(resdata).encode('utf-8')]
        return []
