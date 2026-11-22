"""Aplicacao local HTTP. Sem bibliotecas terceirizadas, custos ou tokens."""
from __future__ import annotations

import argparse
import json
import os
import urllib.error
import urllib.request
import urllib.parse
import webbrowser
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from core import (ROOT, DEFAULT_DB, add_place, add_price, db_connect, export_csv,
                  import_osm, import_prices_csv, list_places, list_prices, seed, stats)

OVERPASS_URL='https://overpass-api.de/api/interpreter'
OVERPASS_QUERY='''[out:json][timeout:20];(node["shop"~"^(farm|farm_shop)$"](around:40000,-22.725,-47.649);way["shop"~"^(farm|farm_shop)$"](around:40000,-22.725,-47.649););out center 100;'''


def discover_osm(con):
    row=con.execute("SELECT value FROM metadata WHERE key='last_osm_refresh'").fetchone()
    if row:
        try:
            if datetime.now(timezone.utc)-datetime.fromisoformat(row[0]) < timedelta(hours=24):
                return {'added':0,'cached':True}
        except ValueError:
            pass
    payload=urllib.parse.urlencode({'data':OVERPASS_QUERY}).encode('utf-8')
    req=urllib.request.Request(OVERPASS_URL,data=payload,headers={'User-Agent':'CestaJustaPiracicaba/0.1 (uso pessoal; consulta manual)','Accept':'application/json'})
    with urllib.request.urlopen(req, timeout=25) as resp:
        if resp.status!=200:
            raise ValueError('OSM respondeu HTTP '+str(resp.status))
        data=json.loads(resp.read(1_500_000).decode('utf-8'))
    if not isinstance(data.get('elements'), list):
        raise ValueError('Resposta OSM inesperada')
    added=import_osm(con,data['elements'])
    con.execute('INSERT OR REPLACE INTO metadata(key,value) VALUES(?,?)',('last_osm_refresh',datetime.now(timezone.utc).isoformat()))
    con.commit()
    return {'added':added,'cached':False}


def create_handler(db_path):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):
            print('[cesta-justa] '+fmt % args)

        def send(self, status, body, ctype='application/json; charset=utf-8', attachment=False):
            data=(json.dumps(body,ensure_ascii=False).encode('utf-8') if ctype.startswith('application/json') else body.encode('utf-8'))
            self.send_response(status)
            self.send_header('Content-Type',ctype)
            self.send_header('Content-Length',str(len(data)))
            self.send_header('X-Content-Type-Options','nosniff')
            self.send_header('Cache-Control','no-store')
            self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; base-uri 'none'; object-src 'none'")
            if attachment:
                self.send_header('Content-Disposition','attachment; filename="precos_cesta_justa.csv"')
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            u=urlsplit(self.path)
            q=parse_qs(u.query)
            path=u.path
            if path=='/':
                return self.send(200,(ROOT/'static'/'index.html').read_text(encoding='utf-8'),'text/html; charset=utf-8')
            if path=='/favicon.ico':
                return self.send(204,'','text/plain')
            try:
                with db_connect(db_path) as con:
                    if path=='/api/places':
                        return self.send(200,list_places(con,q.get('q',[''])[0],q.get('direct',['0'])[0]=='1'))
                    if path=='/api/prices':
                        return self.send(200,list_prices(con,q.get('q',[''])[0],q.get('fresh',['1'])[0]=='1',q.get('wholesale',['0'])[0]=='1'))
                    if path=='/api/stats':
                        return self.send(200,stats(con))
                    if path=='/api/export.csv':
                        return self.send(200,export_csv(con),'text/csv; charset=utf-8',True)
                return self.send(404,{'error':'Rota nao encontrada'})
            except (ValueError, OSError) as e:
                return self.send(400,{'error':str(e)})

        def do_POST(self):
            path=urlsplit(self.path).path
            if path not in ('/api/places','/api/prices','/api/import.csv','/api/discover'):
                return self.send(404,{'error':'Rota nao encontrada'})
            try:
                length=int(self.headers.get('Content-Length',0))
                if length<1 or length>1_100_000:
                    return self.send(413,{'error':'Corpo ausente ou maior que 1,1 MB'})
                data=json.loads(self.rfile.read(length).decode('utf-8'))
                if not isinstance(data,dict):
                    raise ValueError('Objeto JSON esperado')
                with db_connect(db_path) as con:
                    if path=='/api/places':
                        result={'uid':add_place(con,data)}
                    elif path=='/api/prices':
                        result={'added':add_price(con,data)}
                    elif path=='/api/import.csv':
                        result=import_prices_csv(con,str(data.get('csv','')))
                    else:
                        result=discover_osm(con)
                return self.send(200,result)
            except (ValueError,UnicodeError,json.JSONDecodeError) as e:
                return self.send(400,{'error':str(e)})
            except (OSError,urllib.error.URLError,TimeoutError) as e:
                return self.send(503,{'error':'Consulta externa indisponivel: '+str(e)})
    return Handler


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--port',type=int,default=8765)
    p.add_argument('--db',type=Path,default=DEFAULT_DB)
    p.add_argument('--no-browser',action='store_true')
    args=p.parse_args()
    if not (1024<=args.port<=65535):
        p.error('porta deve ser entre 1024 e 65535')
    with db_connect(args.db) as con:
        count=seed(con)
        snapshot=stats(con)
    server=ThreadingHTTPServer(('127.0.0.1',args.port),create_handler(args.db))
    url=f'http://127.0.0.1:{args.port}'
    print(f'Cesta Justa Piracicaba | {url} | locais={snapshot["places"]} | novos={count}',flush=True)
    print('Dados persistidos em: '+str(args.db),flush=True)
    if not args.no_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()

if __name__=='__main__':
    main()
