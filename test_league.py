import unittest
from unittest.mock import patch
import app
class LeagueTests(unittest.TestCase):
    def test_recent_record(self):
        player={'name':'Teste','tag':'#URRCCL8','bestPathOfLegendSeasonResult':{'leagueNumber':7},'currentPathOfLegendSeasonResult':{'leagueNumber':10}}
        self.assertEqual(app.best_league(player),10)
        with patch.object(app,'api_get',return_value=player):
            html=app.app.test_client().get('/players?tag=URRCCL8').get_data(as_text=True)
        self.assertIn('Maior Campeão',html)
        self.assertIn('class="league-10"',html)
    def test_previous_and_historical(self):
        self.assertEqual(app.best_league({'lastPathOfLegendSeasonResult':{'leagueNumber':10},'currentPathOfLegendSeasonResult':{'leagueNumber':1}}),10)
        self.assertEqual(app.best_league({'bestPathOfLegendSeasonResult':{'leagueNumber':10},'currentPathOfLegendSeasonResult':{'leagueNumber':7}}),10)
    def test_missing_invalid(self):
        self.assertEqual(app.best_league({'bestPathOfLegendSeasonResult':None,'currentPathOfLegendSeasonResult':{'leagueNumber':99}}),0)
if __name__=='__main__':unittest.main()
