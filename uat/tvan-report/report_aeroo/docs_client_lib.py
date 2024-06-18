# -*- encoding: utf-8 -*-
import os
import json
import requests
from base64 import b64encode, b64decode
CHUNK_LENGTH = 32*1024
HEADERS = {'content-type': 'application/json'}
DOCSHOST = 'localhost'
DOCSPORT = 8989


class ServerException(Exception):
    pass

class DOCSConnection():
    
    def __init__(self, host=DOCSHOST, port=DOCSPORT, username=None, password=None):
        assert isinstance(host, str) and isinstance(port, (str, int))
        self.host = host
        if isinstance(port, int):
            port = str(port)
        self.port = port
        self.url = 'http://%s:%s/' % (self.host, self.port)
        self.username = username
        self.password = password
    
    def _initpack(self, method):
        return {
                "jsonrpc": "2.0",
                "method": method,
                "id": 1,
                "params": {'username': self.username,'password': self.password},
                    }
    
    def test(self, ctd=None):
        # ctd stands for crash test dummy file
        path = ctd or os.path.join('report_aeroo', 'test_temp.odt')
        with open(path, "r") as testfile:
            data=testfile.read()
        identifier = self.upload(data)
        if not identifier:
            raise ServerException('Upload failded, no upload identifier returned from server.')
        conv_result = self.convert(identifier)
        if not conv_result:
            raise ServerException("Document conversion error.")
        join_result = self.join([identifier, identifier])
        if not join_result:
            raise ServerException("Document join error.")
        return True
        
    def upload(self, data, filename=False):
        assert len(data) > 0
        data = b64encode(data).decode('utf8')
        identifier = False
        data_size = len(data)
        upload_complete = False
        for i in range(0, data_size, CHUNK_LENGTH):
            chunk = data[i:i+CHUNK_LENGTH]
            is_last = (i+CHUNK_LENGTH) >= data_size
            payload = self._initpack('upload')
            payload['params'].update({'data':chunk, 'identifier':identifier,
                                       'is_last': is_last})
            response = requests.post(
                self.url, data = json.dumps(payload), headers=HEADERS).json()
            self._checkerror(response)
            if 'result' not in response:
                break
            elif 'identifier' not in response['result']:
                break
            elif is_last:
                upload_complete = True
            identifier = identifier or response['result']['identifier']
        return identifier or False


    def convert(self, data=False, identifier=False, in_mime=False, out_mime=False):
        payload = self._initpack('convert')
        payload['params'].update({'identifier': identifier})
        if in_mime:
            payload['params'].update({'in_mime': in_mime})
        if out_mime:
            payload['params'].update({'out_mime': out_mime})
        response = requests.post(
            self.url, data = json.dumps(payload), headers=HEADERS).json()
        self._checkerror(response)
        return 'result' in response and b64decode(response['result']) or False
        
    def join(self, idents, in_mime=False, out_mime=False):
        payload = self._initpack('join')
        payload['params'].update({'idents': idents})
        if in_mime:
            payload['params'].update({'in_mime':in_mime})
        if out_mime:
            payload['params'].update({'out_mime':out_mime})
        response = requests.post(
            self.url, data = json.dumps(payload), headers=HEADERS).json()
        self._checkerror(response)
        return 'result' in response and b64decode(response['result']) or False
        
    def _checkerror(self, response):
        if 'error' in response:
            raise ServerException(response['error']['message'])
