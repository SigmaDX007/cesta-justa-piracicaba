import csv
import io
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path
from core import (add_place, add_price, db_connect, export_csv, import_osm,
                  import_prices_csv, list_places, list_prices, normalize, seed, stats)

class CoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.con=db_connect(Path(self.tmp.name)/'test.sqlite')
        seed(self.con)
        self.uid='pref:piracicamirim'
    def tearDown(self):
        self.con.close()
        self.tmp.cleanup()
    def record(self, **overrides):
        row={'place_uid':self.uid,'produto':'Tomate','preco':'8,50','quantidade':'500',
             'unidade':'g','data':date.today().isoformat(),'tipo_evidencia':'observacao_usuario'}
        row.update(overrides)
        return add_price(self.con,row)
    def test_initial_data_has_no_prices(self):
        self.assertGreaterEqual(stats(self.con)['places'],30)
        self.assertEqual(stats(self.con)['prices'],0)
    def test_price_to_kg(self):
        self.assertTrue(self.record())
        r=list_prices(self.con)[0]
        self.assertEqual(r['unit_price'],17)
        self.assertEqual(r['base_unit'],'kg')
    def test_units_dozen(self):
        self.record(produto='Ovo',preco='12',quantidade='1',unidade='duzia')
        r=list_prices(self.con,'ovo')[0]
        self.assertEqual(r['base_unit'],'un')
        self.assertEqual(r['unit_price'],1)
    def test_idempotence(self):
        self.record();self.assertFalse(self.record())
        self.assertEqual(stats(self.con)['prices'],1)
    def test_future_date_rejected(self):
        with self.assertRaisesRegex(ValueError,'futura'):
            self.record(data=(date.today()+timedelta(days=1)).isoformat())
    def test_wholesale_excluded_default(self):
        self.record(tipo_evidencia='referencia_atacado',fonte_url='https://ceagesp.gov.br/cotacoes')
        self.assertEqual(list_prices(self.con),[])
        self.assertEqual(len(list_prices(self.con,include_wholesale=True)),1)
    def test_public_url_required(self):
        with self.assertRaisesRegex(ValueError,'URL'):
            self.record(tipo_evidencia='anuncio_publico')
    def test_stale_hidden(self):
        self.record(data=(date.today()-timedelta(days=8)).isoformat())
        self.assertEqual(list_prices(self.con),[])
        self.assertEqual(len(list_prices(self.con,fresh=False)),1)
    def test_csv_partial_and_export(self):
        content='place_uid;produto;preco;quantidade;unidade;data\n'+f'{self.uid};Banana;5;1;kg;{date.today()}\n'+f'unknown;Abacate;3;1;kg;{date.today()}\n'
        result=import_prices_csv(self.con,content)
        self.assertEqual(result['added'],1)
        self.assertEqual(len(result['errors']),1)
        self.assertIn('Banana',export_csv(self.con))
    def test_manual_supplier_unverified(self):
        uid=add_place(self.con,{'name':'Horta Teste','kind':'produtor','city':'Rio das Pedras'})
        r=next(x for x in list_places(self.con,direct=True) if x['uid']==uid)
        self.assertEqual(r['status'],'cadastrado_sem_verificacao')
    def test_osm_idempotence(self):
        el=[{'type':'node','id':12,'lat':-22.72,'lon':-47.65,'tags':{'shop':'farm','name':'Horta Exemplo'}}]
        self.assertEqual(import_osm(self.con,el),1)
        self.assertEqual(import_osm(self.con,el),0)
    def test_normalization(self):
        self.assertEqual(normalize('  Maçã  Gala '),'maca gala')
    def test_csv_formula_injection_escaped(self):
        self.record(produto='=1+1')
        self.assertIn("'=1+1", export_csv(self.con))
    def test_source_url_script_rejected(self):
        with self.assertRaisesRegex(ValueError,'URL'):
            self.record(tipo_evidencia='anuncio_publico',fonte_url='javascript:alert(1)')

if __name__=='__main__':unittest.main()
