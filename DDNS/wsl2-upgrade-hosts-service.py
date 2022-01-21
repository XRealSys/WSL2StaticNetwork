#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import io
import re
from aiohttp import web

WINDOWS_HOSTS_FILE_DIR = 'C:\\Windows\\System32\\drivers\\etc\\hosts'
WSL2DOMAINS = ['ubuntu.wsl2.local']
WEB_ROUTERS = web.RouteTableDef()

class HostsFile(object):
    def __init__(self) -> None:
        super().__init__()
        self.records = {}
        self.lines = []
        self.read_and_encode_file()
       
    def read_and_encode_file(self):
        with io.open(WINDOWS_HOSTS_FILE_DIR, 'r') as f:
            contents = f.read()
            self.lines = contents.split('\n')
            idx = 0
            for line in self.lines:
                if len(line) > 0 and line[0] != '#':
                    params = line.split('\t')
                    if len(params) == 2 and params[1] in WSL2DOMAINS:
                        self.records[idx] = {
                            'ip': params[0],
                            'domain': params[1]
                        }
                idx += 1
    
    def upgrade(self, domain, ip):
        exists = False
        if domain in WSL2DOMAINS:
            try:
                with io.open(WINDOWS_HOSTS_FILE_DIR, 'w') as f:
                    idx = 0
                    for line in self.lines:
                        if idx in self.records:
                            if self.records[idx]['domain'] == domain:
                                self.records[idx]['ip'] = ip
                                exists = True
                            f.write('{0}\t{1}\n'.format(
                                self.records[idx]['ip'], 
                                self.records[idx]['domain']
                            ))
                            print('Info: upgrade record {0} {1}'.format(
                                self.records[idx]['ip'], 
                                self.records[idx]['domain']
                            ))
                        else:
                            f.write('{0}\n'.format(line))
                        idx += 1
                    if not exists:
                        f.write('{0}\t{1}\n'.format(ip, domain))
                        print('Info: add record {0} {1}'.format(ip, domain))
                return True
            except IOError as e:
                print('Error: {0}'.format(e))
                return False
        else:
            print('Warning: invalid domain')
            return False
    
    @staticmethod
    def open():
        try:
            return HostsFile()
        except IOError as e:
            print('Error: {0}'.format(e))
            return False
     
if __name__ == '__main__':
    hosts = HostsFile.open()

    @WEB_ROUTERS.get(path='/wsl2ddns')       
    async def handler(request: web.Request):
        ip_check = re.match(r'^((2(5[0-5]|[0-4]\d))|[0-1]?\d{1,2})(\.((2(5[0-5]|[0-4]\d))|[0-1]?\d{1,2})){3}$', request.query['ip']) \
                    if 'ip' in request.query else False
        domain_check = len(request.query['domain']) > 0 \
                    if 'domain' in request.query else False
        if ip_check and domain_check:
            answer = hosts.upgrade(
                domain=request.query['domain'],
                ip=request.query['ip'])
            return web.Response(text='success') \
                if answer else web.Response(status=500, text='upgrade failed')
        else:
            return web.Response(status=500, text='invalid patermeters')
        
    app = web.Application()
    app.add_routes(WEB_ROUTERS)
    web.run_app(app=app, port=8448)