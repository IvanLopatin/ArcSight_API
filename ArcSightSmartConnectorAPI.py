#!/usr/bin/python
# Hewlett-Packard Enterprise
# Author: Henrique Goncalves <henrique.goncalves@hpe.com>
# ArcSight Smart Connector API


import requests
import json
import csv
from xml.etree import ElementTree
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import argparse

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

class ArcSightSmartConnectorAPI(object):
    
    def __init__(self, host, port):
        self.session = requests.Session()
        self.host = host
        self.port = port
        self.logged_in = False
        self.url = 'https://{host}:{port}/cwsapi/services/v1?wsdl'.format(host=host,port=port)

    def soap_request(self, rtype, body=None):                                                                                                         
        headers = {'Content-Type': 'text/xml', 'Content-Lenght': len(body), 'SOAPAction': ''}
        if rtype == 'GET':
            return self.session.get(self.url, headers=headers, verify=False)
        elif rtype == 'POST':
            return self.session.post(self.url, headers=headers, data=body,  verify=False)


        
    def login(self, user, password):
        body = '''
<soapenv:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:v1="http://v1.soap.loadable.arcsight.com">
   <soapenv:Header/>
   <soapenv:Body>
      <v1:login soapenv:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
         <in0 xsi:type="soapenc:string" xmlns:soapenc="http://schemas.xmlsoap.org/soap/encoding/">{username}</in0>
         <in1 xsi:type="soapenc:string" xmlns:soapenc="http://schemas.xmlsoap.org/soap/encoding/">{password}</in1>
      </v1:login>
   </soapenv:Body>
</soapenv:Envelope>'''.format(username=user,password=password)
        response = self.soap_request('POST', body)
        xml = ElementTree.fromstring(response.content)
        if xml[0][1].text == 'true':
            self.logged_in = True

    def getSystemInfo(self):
        if not self.logged_in:
            raise Exception('Authentication Required!')
        body = '''
<soapenv:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:v1="http://v1.soap.loadable.arcsight.com">
   <soapenv:Header/>
   <soapenv:Body>
      <v1:getSystemInfo soapenv:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/"/>
   </soapenv:Body>
</soapenv:Envelope>'''

        response = self.soap_request('POST', body)
        xml = ElementTree.fromstring(response.content)
        return xml


    def getMemory(self, unit='bytes'):
        xml = self.getSystemInfo()
        for item in xml[0][1]:
            if item[0].text == 'Memory':
                text = item[1].text
                info = text.split()[2].strip('(').strip(')').split('/')
                if unit == 'bytes':
                    memory = {'used': int(info[0]), 'free': int(info[1])}
                elif unit == 'mbytes':
                    memory = {'used': round(int(info[0])/1024/1024), 'free': round(int(info[1])/1024/1024)}
                memory['unit'] = unit
                return memory

    def formatOutput(self, result, format='dict'):
        if format == 'dict':
            return result
        elif format == 'csv':
            csvfile = StringIO('')
            writer = csv.DictWriter(csvfile, fieldnames=result.keys())
            writer.writeheader()
            writer.writerows([result])

            return csvfile.getvalue()
        elif format == 'json':
            return json.dumps(result)



if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser._optionals.title = "flag arguments"
    parser.add_argument('--host', help='Host where the connector is listening on', type=str, required=True)
    parser.add_argument('--port', help='Port where the connector is listening on', type=int, required=True)
    parser.add_argument('--user', help='Connector Remote Management User', type=str, default='connector_user')
    parser.add_argument('--password', help='Connector Remote Management Password', type=str, default='change_me')
    parser.add_argument('--command', help='SOAP command to execute', type=str, choices=['getMemory'], required=True)
    parser.add_argument('--format',  help='Output format', type=str, choices=['csv', 'dict', 'json'], default='dict')
    args = parser.parse_args()


    assc = ArcSightSmartConnectorAPI(args.host, args.port)
    assc.login(args.user, args.password)
    
    if args.command == 'getMemory':
        print(assc.formatOutput(assc.getMemory('mbytes'), args.format))
