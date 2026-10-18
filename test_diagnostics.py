import unittest
from unittest.mock import patch, Mock
import app
class DiagnosticsTests(unittest.TestCase):
    def test_access_error_is_safe_and_useful(self):
        response=Mock(status_code=403)
        response.json.return_value={'reason':'accessDenied.invalidIp','message':'SECRET'}
        with patch.object(app.requests,'get',return_value=response), self.assertLogs(app.app.logger,level='WARNING') as logs:
            with self.assertRaisesRegex(app.APIError,'autorizar'): app._fetch_api(app.API_URL_CARDS)
        text=' '.join(logs.output)
        self.assertIn('HTTP 403',text)
        self.assertIn('accessDenied.invalidIp',text)
        self.assertNotIn('SECRET',text)
    def test_non_json_rate_limit(self):
        response=Mock(status_code=429)
        response.json.side_effect=ValueError()
        with patch.object(app.requests,'get',return_value=response):
            with self.assertRaisesRegex(app.APIError,'Muitas consultas'): app._fetch_api(app.API_URL_CARDS)
if __name__=='__main__': unittest.main()
