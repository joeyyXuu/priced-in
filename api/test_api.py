"""Integration tests against the real local database, using the API reader role."""
import unittest
import psycopg
from fastapi.testclient import TestClient
from api.main import app,connection


class APITests(unittest.TestCase):
    def setUp(self):
        self.client=TestClient(app)

    def test_health_and_docs(self):
        self.assertEqual(self.client.get('/health').json(),{'status':'ok'})
        self.assertEqual(self.client.get('/docs').status_code,200)
        self.assertIn('/events/{candidate_id}/prices',self.client.get('/openapi.json').json()['paths'])

    def test_sample_and_filters(self):
        self.assertEqual(self.client.get('/events').json()['total'],20)
        self.assertEqual(self.client.get('/events?pattern=divergent').json()['total'],8)
        self.assertEqual(self.client.get('/events?pattern=aligned').json()['total'],3)
        self.assertEqual(self.client.get('/events?event_type=macro').json()['total'],3)
        self.assertEqual(self.client.get('/events?ticker=TSM').json()['total'],2)
        self.assertEqual(len(self.client.get('/filters').json()['years']),7)
        first=self.client.get('/events?limit=1&offset=0').json()['items'][0]
        second=self.client.get('/events?limit=1&offset=1').json()['items'][0]
        self.assertNotEqual(first['candidate_id'],second['candidate_id'])

    def test_detail_and_nulls(self):
        row=self.client.get('/events/C04').json()
        self.assertEqual(row['metrics']['eps_surprise_pct'],6.25)
        self.assertEqual(row['metrics']['calculated_pattern'],'divergent')
        for cid in ['C19','C25']:
            row=self.client.get('/events/'+cid).json()
            self.assertIsNone(row['metrics']['eps_surprise_pct'])
            self.assertIsNone(row['metrics']['calculated_pattern'])
            self.assertFalse(row['estimate']['comparability_verified'])
            self.assertEqual(row['estimate']['actual_eps_basis'],'tifrs')

    def test_price_window(self):
        row=self.client.get('/events/C12/prices').json()
        self.assertEqual(row['benchmark'],'SPY')
        self.assertEqual(len(row['items']),130)
        self.assertEqual({r['ticker'] for r in row['items']},{'SOXX','SPY'})
        self.assertEqual(len({r['price_date'] for r in row['items']}),65)
        self.assertTrue(all(r['adjusted_close'] is not None for r in row['items']))

    def test_invalid_and_missing(self):
        for url in ['/events?limit=0','/events?year=2000', '/events?ticker=INVALID', '/events/C04/prices?before=999']:
            self.assertEqual(self.client.get(url).status_code,422)
        self.assertEqual(self.client.get('/events/C99').status_code,404)
        self.assertEqual(self.client.get("/events/C01%27%20OR%20%271%27=%271").status_code,404)
        self.assertEqual(self.client.post('/events',json={}).status_code,405)

    def test_database_write_denied(self):
        gen=connection()
        conn=next(gen)
        try:
            conn.execute('SET TRANSACTION READ WRITE')
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                conn.execute("UPDATE events SET headline=headline WHERE candidate_id='C01'")
            conn.rollback()
        finally:
            gen.close()

    def test_unavailable_database(self):
        def unavailable():
            raise psycopg.OperationalError('secret connection details')
        app.dependency_overrides[connection]=unavailable
        try:
            response=self.client.get('/events')
            self.assertEqual(response.status_code,503)
            self.assertNotIn('secret',response.text)
        finally:
            app.dependency_overrides.clear()


if __name__=='__main__':
    unittest.main(verbosity=2)
