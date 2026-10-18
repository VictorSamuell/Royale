import sys, unittest
from pathlib import Path
from unittest.mock import patch
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, str(Path(__file__).resolve().parent))
import app
class CacheTests(unittest.TestCase):
    def setUp(self): app._cache.clear()
    def test_hit_and_copy(self):
        with patch.object(app, '_fetch_api', return_value={'items':[{'name':'Knight'}]}) as fetch:
            app.api_get(app.API_URL_CARDS)['items'][0]['name']='changed'
            self.assertEqual(app.api_get(app.API_URL_CARDS)['items'][0]['name'], 'Knight')
            self.assertEqual(fetch.call_count,1)
    def test_expiration(self):
        for url, ttl in [(app.API_URL_CARDS,3600),(app.API_URL_PLAYER+'%23URRCCL8',60)]:
            app._cache.clear()
            with patch.object(app, 'monotonic', return_value=0) as clock, patch.object(app, '_fetch_api', return_value={}) as fetch:
                app.api_get(url)
                clock.return_value=ttl-1
                app.api_get(url)
                self.assertEqual(fetch.call_count,1)
                clock.return_value=ttl
                app.api_get(url)
                self.assertEqual(fetch.call_count,2)
    def test_errors_not_cached(self):
        with patch.object(app, '_fetch_api', side_effect=[app.APIError('offline'), {'ok':True}]) as fetch:
            with self.assertRaises(app.APIError): app.api_get('player')
            self.assertTrue(app.api_get('player')['ok'])
            self.assertEqual(fetch.call_count,2)
    def test_bounded(self):
        with patch.object(app, '_fetch_api', return_value={}):
            for i in range(app.MAX_CACHE_ENTRIES+10): app.api_get(str(i))
        self.assertEqual(len(app._cache),app.MAX_CACHE_ENTRIES)
    def test_concurrent(self):
        with patch.object(app, '_fetch_api', return_value={'ok':True}) as fetch:
            with ThreadPoolExecutor(max_workers=8) as pool:
                results=list(pool.map(app.api_get,['same']*20))
            self.assertEqual(fetch.call_count,1)
            self.assertTrue(all(r['ok'] for r in results))
if __name__=='__main__': unittest.main()
