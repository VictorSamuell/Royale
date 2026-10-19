import unittest
from unittest.mock import patch
import app
class ChampionTests(unittest.TestCase):
    def test_seasons_stay_separate(self):
        p={'name':'Teste','tag':'#URRCCL8','currentPathOfLegendSeasonResult':{'leagueNumber':4,'trophies':50},'lastPathOfLegendSeasonResult':{'leagueNumber':7,'trophies':1696,'rank':None},'bestPathOfLegendSeasonResult':{'leagueNumber':7,'trophies':2000,'rank':1234}}
        results=app.champion_results(p)
        self.assertEqual([r['score'] for r in results],[1696,2000])
        self.assertEqual([r['rank'] for r in results],[None,1234])
        with patch.object(app,'api_get',return_value=p):
            html=app.app.test_client().get('/players?tag=URRCCL8').get_data(as_text=True)
        self.assertIn('1.696',html)
        self.assertIn('Ranking global: #1.234',html)
        self.assertNotIn('top 1%',html.lower())
    def test_missing_zero_legacy(self):
        self.assertEqual(app.champion_results({}),[])
        self.assertEqual(app.champion_results({'lastPathOfLegendSeasonResult':None}),[])
        rows=app.champion_results({'bestPathOfLegendSeasonResult':{'leagueNumber':10,'trophies':0,'rank':0}})
        self.assertEqual(rows[0]['score'],0)
        self.assertIsNone(rows[0]['rank'])
if __name__=='__main__':unittest.main()
