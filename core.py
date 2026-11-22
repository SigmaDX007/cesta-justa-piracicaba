"""Persistencia e comparacao auditavel de precos de alimentos (somente stdlib)."""
from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import sqlite3
import unicodedata
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
DEFAULT_DB = Path.home() / '.cesta_justa_piracicaba' / 'cesta.sqlite'
UNIT_FACTORS = {'kg': ('kg', 1), 'g': ('kg', .001), 'l': ('l', 1), 'ml': ('l', .001), 'un': ('un', 1), 'duzia': ('un', 12)}
OFFICIAL_URL = 'https://piracicaba.sp.gov.br/servicos/varejoes-municipais-e-feiras-livres/'


def normalize(value):
    s = unicodedata.normalize('NFKD', str(value or '').lower())
    s = ''.join(c for c in s if not unicodedata.combining(c))
    return ' '.join(re.findall(r'[a-z0-9]+', s))


def num(value, name, allow_zero=False):
    try:
        v = float(str(value).strip().replace('R$', '').replace(' ', '').replace(',', '.'))
    except (TypeError, ValueError):
        raise ValueError(f'{name}: numero invalido') from None
    if not (0 <= v < 1_000_000 if allow_zero else 0 < v < 1_000_000):
        raise ValueError(f'{name}: fora do intervalo permitido')
    return v


def safe_url(value):
    value = str(value or '').strip()
    if not value:
        return ''
    parsed = urlparse(value)
    if parsed.scheme not in ('http', 'https') or not parsed.netloc or parsed.username or parsed.password:
        raise ValueError('URL da fonte deve usar HTTP(S), sem credenciais')
    return value[:1000]


def db_connect(path=DEFAULT_DB):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(path))
    con.row_factory = sqlite3.Row
    con.execute('PRAGMA busy_timeout=5000')
    con.execute('PRAGMA foreign_keys=ON')
    con.execute('PRAGMA journal_mode=WAL')
    con.executescript('''
    CREATE TABLE IF NOT EXISTS places (
      uid TEXT PRIMARY KEY, name TEXT NOT NULL, kind TEXT NOT NULL,
      city TEXT NOT NULL, address TEXT NOT NULL DEFAULT '', schedule TEXT NOT NULL DEFAULT '',
      url TEXT NOT NULL DEFAULT '', source_date TEXT NOT NULL DEFAULT '',
      status TEXT NOT NULL, direct_candidate INTEGER NOT NULL DEFAULT 0,
      lat REAL, lon REAL, updated_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS prices (
      fingerprint TEXT PRIMARY KEY, place_uid TEXT NOT NULL REFERENCES places(uid),
      product TEXT NOT NULL, product_key TEXT NOT NULL, variation TEXT NOT NULL DEFAULT '',
      price REAL NOT NULL, quantity REAL NOT NULL, unit TEXT NOT NULL,
      unit_price REAL NOT NULL, base_unit TEXT NOT NULL,
      observed_date TEXT NOT NULL, source_url TEXT NOT NULL,
      evidence_type TEXT NOT NULL, delivery_fee REAL NOT NULL DEFAULT 0,
      note TEXT NOT NULL DEFAULT '', recorded_at TEXT NOT NULL
    );
    CREATE INDEX IF NOT EXISTS ix_prices_product ON prices(product_key, base_unit, observed_date);
    CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
    ''')
    con.commit()
    return con


def seed(con, csv_path=ROOT / 'data' / 'places.csv'):
    count = 0
    with open(csv_path, encoding='utf-8-sig', newline='') as f:
        for row in csv.DictReader(f):
            con.execute('''INSERT OR IGNORE INTO places
              (uid,name,kind,city,address,schedule,url,source_date,status,direct_candidate,updated_at)
              VALUES (?,?,?,?,?,?,?,?,?,?,?)''',
              (row['uid'], row['name'], row['kind'], row['city'], row['address'], row['schedule'],
               row['url'], row['source_date'], row['status'], int(row['direct_candidate']), datetime.now(timezone.utc).isoformat()))
            count += con.execute('SELECT changes()').fetchone()[0]
    con.commit()
    return count


def add_place(con, data):
    name = str(data.get('name', '')).strip()[:180]
    if len(name) < 3:
        raise ValueError('Informe nome do local ou produtor')
    kind = str(data.get('kind', 'produtor'))
    if kind not in ('produtor', 'feira', 'varejao', 'mercado', 'loja'):
        raise ValueError('Tipo de estabelecimento invalido')
    city = str(data.get('city', 'Piracicaba')).strip()[:100]
    address = str(data.get('address', '')).strip()[:300]
    url = safe_url(data.get('url'))
    uid = 'manual:' + hashlib.sha256((normalize(name)+'|'+normalize(city)+'|'+normalize(address)).encode()).hexdigest()[:16]
    con.execute('''INSERT OR IGNORE INTO places
    (uid,name,kind,city,address,schedule,url,source_date,status,direct_candidate,updated_at)
    VALUES(?,?,?,?,?,?,?,?,?,?,?)''', (uid,name,kind,city,address,'',url,date.today().isoformat(),
                                      'cadastrado_sem_verificacao',int(kind=='produtor'),datetime.now(timezone.utc).isoformat()))
    con.commit()
    return uid


def add_price(con, row):
    uid = str(row.get('place_uid', '')).strip()
    if not con.execute('SELECT 1 FROM places WHERE uid=?', (uid,)).fetchone():
        raise ValueError('Local nao cadastrado: ' + uid)
    product = str(row.get('produto', '')).strip()[:120]
    if len(normalize(product)) < 2:
        raise ValueError('Produto obrigatorio')
    variation = str(row.get('variacao', '')).strip()[:120]
    price = num(row.get('preco'), 'Preco')
    qty = num(row.get('quantidade', 1), 'Quantidade')
    unit = str(row.get('unidade', '')).strip().lower()
    if unit not in UNIT_FACTORS:
        raise ValueError('Unidade valida: kg, g, l, ml, un, duzia')
    base_unit, factor = UNIT_FACTORS[unit]
    when = str(row.get('data', date.today().isoformat())).strip()
    try:
        observed = date.fromisoformat(when)
    except ValueError:
        raise ValueError('Data no formato AAAA-MM-DD') from None
    if observed > date.today() or observed < date(2020, 1, 1):
        raise ValueError('Data nao pode ser futura nem anterior a 2020')
    evidence = str(row.get('tipo_evidencia', 'observacao_usuario')).strip()
    if evidence not in ('observacao_usuario', 'anuncio_publico', 'cotacao_produtor', 'referencia_atacado'):
        raise ValueError('Tipo de evidencia invalido')
    source = safe_url(row.get('fonte_url'))
    if evidence in ('anuncio_publico', 'referencia_atacado') and not source:
        raise ValueError('Anuncio e atacado exigem URL da fonte')
    delivery_fee = num(row.get('frete') or 0, 'Frete', allow_zero=True)
    note = str(row.get('observacao', '')).strip()[:500]
    digest = '|'.join((uid,normalize(product),normalize(variation),f'{price:.4f}',f'{qty:.4f}',unit,when,source,evidence))
    fingerprint = hashlib.sha256(digest.encode()).hexdigest()
    con.execute('''INSERT OR IGNORE INTO prices
      (fingerprint,place_uid,product,product_key,variation,price,quantity,unit,unit_price,
       base_unit,observed_date,source_url,evidence_type,delivery_fee,note,recorded_at)
      VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
      (fingerprint,uid,product,normalize(product),variation,price,qty,unit,round(price/(qty*factor),4),
       base_unit,when,source,evidence,delivery_fee,note,datetime.now(timezone.utc).isoformat()))
    added = con.execute('SELECT changes()').fetchone()[0] == 1
    con.commit()
    return added


def list_places(con, query='', direct=False):
    sql = 'SELECT * FROM places WHERE 1=1'
    args = []
    if query:
        sql += ' AND (lower(name) LIKE ? OR lower(city) LIKE ? OR lower(address) LIKE ?)'
        text = '%' + query.lower().strip() + '%'
        args.extend([text] * 3)
    if direct:
        sql += ' AND direct_candidate=1'
    sql += ' ORDER BY direct_candidate DESC, kind, name LIMIT 400'
    return [dict(r) for r in con.execute(sql,args).fetchall()]


def list_prices(con, product='', fresh=True, include_wholesale=False, days=7):
    sql = '''SELECT p.*, l.name AS place_name, l.kind AS place_kind, l.direct_candidate,
      l.city, l.address FROM prices p JOIN places l ON l.uid=p.place_uid WHERE 1=1'''
    args=[]
    if product:
        sql += ' AND p.product_key LIKE ?'
        args.append('%'+normalize(product)+'%')
    if fresh:
        sql += ' AND p.observed_date>=?'
        args.append((date.today()-timedelta(days=days)).isoformat())
    if not include_wholesale:
        sql += " AND p.evidence_type!='referencia_atacado'"
    sql += ' ORDER BY p.product_key, p.variation, p.base_unit, p.unit_price, p.observed_date DESC LIMIT 500'
    return [dict(r) for r in con.execute(sql,args).fetchall()]


def stats(con):
    n = lambda table: con.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]
    prod = con.execute('SELECT COUNT(*) FROM places WHERE direct_candidate=1').fetchone()[0]
    recent = con.execute('SELECT COUNT(*) FROM prices WHERE observed_date>=? AND evidence_type!=?',
        ((date.today()-timedelta(days=7)).isoformat(),'referencia_atacado')).fetchone()[0]
    osm = con.execute("SELECT value FROM metadata WHERE key='last_osm_refresh'").fetchone()
    return {'places':n('places'), 'producer_leads':prod,'prices':n('prices'),
            'recent_comparable_prices':recent,'last_osm_refresh':osm[0] if osm else None}


def import_prices_csv(con, content):
    if len(content.encode('utf-8')) > 1_000_000:
        raise ValueError('CSV maior que 1 MB')
    if '\x00' in content:
        raise ValueError('CSV com bytes nulos')
    reader = csv.DictReader(io.StringIO(content.lstrip('\ufeff')),delimiter=';')
    required={'place_uid','produto','preco','quantidade','unidade','data'}
    if not reader.fieldnames or not required.issubset(reader.fieldnames):
        raise ValueError('Cabecalhos obrigatorios: '+', '.join(sorted(required)))
    added=0
    errors=[]
    for idx,row in enumerate(reader,2):
        if idx>502:
            errors.append('Limite de 500 linhas por importacao')
            break
        try:
            added+=int(add_price(con,row))
        except ValueError as e:
            errors.append(f'Linha {idx}: {e}')
    return {'added':added,'errors':errors[:50]}


def export_csv(con):
    columns=['place_uid','produto','variacao','preco','quantidade','unidade','data','fonte_url','tipo_evidencia','frete','observacao']
    out=io.StringIO()
    writer=csv.writer(out, delimiter=';')
    writer.writerow(columns)
    for r in con.execute('''SELECT place_uid,product,variation,price,quantity,unit,observed_date,
        source_url,evidence_type,delivery_fee,note FROM prices ORDER BY observed_date DESC'''):
        writer.writerow(["'" + str(x) if isinstance(x, str) and x.lstrip().startswith(('=', '+', '-', '@')) else x for x in r])
    return '\ufeff'+out.getvalue()


def import_osm(con, elements):
    """Cadastro de potenciais pontos de venda, NUNCA os certifica como produtores."""
    added=0
    for e in elements[:100]:
        tag=e.get('tags',{})
        name=str(tag.get('name','')).strip()[:180]
        if not name or tag.get('shop') not in ('farm','farm_shop'):
            continue
        lat=e.get('lat',e.get('center',{}).get('lat'))
        lon=e.get('lon',e.get('center',{}).get('lon'))
        if not isinstance(lat,(float,int)) or not isinstance(lon,(float,int)):
            continue
        uid=f"osm:{e.get('type','node')}:{e.get('id')}"
        addr=' '.join(str(tag.get(k,'')) for k in ('addr:street','addr:housenumber')).strip()
        source=f"https://www.openstreetmap.org/{e.get('type','node')}/{e.get('id')}"
        con.execute('''INSERT OR IGNORE INTO places (uid,name,kind,city,address,schedule,url,source_date,
            status,direct_candidate,lat,lon,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)''',
            (uid,name,'loja','Piracicaba e regiao',addr,'',source,date.today().isoformat(),
             'osm_nao_verificado',1,float(lat),float(lon),datetime.now(timezone.utc).isoformat()))
        added+=con.execute('SELECT changes()').fetchone()[0]
    con.commit()
    return added
