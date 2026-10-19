import unittest
from unittest.mock import patch
import app
from profile_tools import deck_info, battle_rows, normalize_tag
CARDS=[{'id':26000000+i,'name':f'Card {i}','elixirCost':3,'iconUrls':{'medium':'https://example.com/card.png'}} for i in range(8)]
class ProfileToolsTests(unittest.TestCase):
 def test_deck_link(self):
  deck=deck_info(CARDS)
  self.assertEqual(deck['average'],3)
  self.assertIn('26000000%3B26000001',deck['link'])
  self.assertIsNone(deck_info(CARDS[:7])['link'])
  self.assertIsNone(deck_info([CARDS[0]]*8)['link'])
  self.assertIsNone(deck_info([])['average'])
 def test_comparison_and_partial_failure(self):
  p={'name':'A','tag':'#2PP','currentDeck':CARDS,'currentPathOfLegendSeasonResult':{'leagueNumber':7,'trophies':1696}}
  with patch.object(app,'api_get',side_effect=[p,app.APIError('offline')]):
   response=app.app.test_client().get('/compare?a=2PP&b=2QQ')
  self.assertEqual(response.status_code,200)
  html=response.get_data(as_text=True)
  self.assertIn('1696',html);self.assertIn('offline',html);self.assertIn('Copiar deck',html)
 def test_invalid_tag_no_request(self):
  with patch.object(app,'api_get') as api:
   app.app.test_client().get('/battles?tag=invalid')
   api.assert_not_called()
  self.assertEqual(normalize_tag(' urrccl8 '),'#URRCCL8')
 def test_battle_results_and_historical_decks(self):
  battle={'battleTime':'20261018T120000.000Z','team':[{'tag':'#2PP','crowns':2,'cards':CARDS}],'opponent':[{'tag':'#2QQ','name':'Opponent','crowns':1,'cards':CARDS}]}
  rows=battle_rows([battle],'#2PP')
  self.assertEqual(rows[0]['result'],'Vitória');self.assertEqual(len(rows[0]['deck']['cards']),8)
  battle['opponent'][0]['crowns']=2
  self.assertNotEqual(battle_rows([battle],'#2PP')[0]['result'],'Vitória')
  battle['team'].append({'tag':'#2GG','crowns':3})
  self.assertEqual(battle_rows([battle],'#2PP')[0]['style'],'unknown')
  with patch.object(app,'api_get',return_value=[battle]):
   self.assertEqual(app.app.test_client().get('/battles?tag=2PP').status_code,200)
 def test_missing_data_pages(self):
  self.assertEqual(app.app.test_client().get('/compare').status_code,200)
  with patch.object(app,'api_get',return_value={'name':'A','tag':'#2PP'}):
   response=app.app.test_client().get('/players?tag=2PP')
   self.assertIn('Deck não informado',response.get_data(as_text=True))
  with patch.object(app,'api_get',return_value=[]):
   self.assertIn('Nenhuma batalha',app.app.test_client().get('/battles?tag=2PP').get_data(as_text=True))
if __name__=='__main__':unittest.main()
