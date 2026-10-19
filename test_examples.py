import unittest
from unittest.mock import patch
import app
class ExampleTests(unittest.TestCase):
 def test_page_does_not_fetch_rankings(self):
  with patch.object(app,'api_get') as api:
   html=app.app.test_client().get('/players').get_data(as_text=True)
   api.assert_not_called()
   self.assertIn('URRCCL8',html)
 def test_top_links(self):
  with patch.object(app,'api_get',return_value={'items':[{'name':'Top','tag':'#2PP','rank':1}]}):
   data=app.app.test_client().get('/examples/top').get_json()
   self.assertEqual(data['players'][0]['url'],'/players?tag=%232PP')
 def test_failure(self):
  with patch.object(app,'api_get',side_effect=app.APIError('offline')):
   self.assertEqual(app.app.test_client().get('/examples/top').status_code,503)
if __name__=='__main__': unittest.main()
