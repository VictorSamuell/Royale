from flask import Flask, render_template, request, redirect, url_for
import requests
import os
import re
from collections import OrderedDict
from copy import deepcopy
from threading import Lock
from time import monotonic
from dotenv import load_dotenv
from urllib.parse import quote

load_dotenv()
app = Flask(__name__)
API_URL_CARDS = 'https://api.clashroyale.com/v1/cards'
API_URL_PLAYER = 'https://api.clashroyale.com/v1/players/'
HEADERS = {'Authorization': f"Bearer {os.getenv('API_TOKEN')}"}
RARITIES = {'Common': 'Comum', 'Rare': 'Rara', 'Epic': 'Épica', 'Legendary': 'Lendária', 'Champion': 'Campeão'}
LEAGUES = dict(enumerate(['Desafiante I', 'Desafiante II', 'Desafiante III', 'Mestre I', 'Mestre II', 'Mestre III', 'Campeão', 'Grande Campeão', 'Campeão Real', 'Maior Campeão'], 1))

class APIError(Exception):
    pass

_cache = OrderedDict()
_cache_lock = Lock()
_fetch_locks = [Lock() for _ in range(32)]
MAX_CACHE_ENTRIES = 256

def api_get(url):
    ttl = 3600 if url == API_URL_CARDS else 60
    with _fetch_locks[hash(url) % len(_fetch_locks)]:
        with _cache_lock:
            entry = _cache.get(url)
            if entry and monotonic() < entry[0]:
                _cache.move_to_end(url)
                return deepcopy(entry[1])
            _cache.pop(url, None)
        data = _fetch_api(url)
        with _cache_lock:
            _cache[url] = (monotonic() + ttl, deepcopy(data))
            _cache.move_to_end(url)
            while len(_cache) > MAX_CACHE_ENTRIES:
                _cache.popitem(last=False)
        return data

def _fetch_api(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=(3.05, 8))
        if response.status_code == 404:
            raise APIError('Jogador não encontrado. Confira a tag no perfil do jogo.')
        response.raise_for_status()
        return response.json()
    except (requests.RequestException, ValueError) as exc:
        app.logger.warning('Falha na consulta à API: %s', type(exc).__name__)
        raise APIError('O serviço do Clash Royale está indisponível no momento. Tente novamente em instantes.') from exc

@app.route('/')
def index():
    search = request.args.get('search', '').strip()
    rarity = request.args.get('rarity', '')
    sort = request.args.get('sort', '')
    error = None
    cards = []
    try:
        cards = api_get(API_URL_CARDS).get('items', [])
        for card in cards:
            card['rarity'] = (card.get('rarity') or '').capitalize()
        if search:
            cards = [c for c in cards if search.casefold() in c.get('name', '').casefold()]
        if rarity:
            cards = [c for c in cards if c['rarity'].lower() == rarity.lower()]
        if sort == 'rarity':
            order = list(RARITIES)
            cards.sort(key=lambda c: order.index(c['rarity']) if c['rarity'] in order else len(order))
        elif sort == 'elixir':
            cards.sort(key=lambda c: c.get('elixirCost') if c.get('elixirCost') is not None else float('inf'))
        elif sort == 'name':
            cards.sort(key=lambda c: c.get('name', '').casefold())
    except APIError as exc:
        error = str(exc)
    return render_template('cards.html', cards=cards, search=search, rarity=rarity, sort=sort, rarity_labels=RARITIES, error=error)

@app.route('/players', methods=['GET', 'POST'])
def players():
    if request.method == 'POST':
        return redirect(url_for('players', tag=request.form.get('player_tag', '').strip()))
    tag = request.args.get('tag', '').strip().upper()
    player = None
    error = None
    league_name = 'Sem registro'
    winrate = 0
    if tag:
        tag = '#' + tag.lstrip('#')
        if not re.fullmatch(r'#[0289PYLQGRJCUV]{3,15}', tag):
            error = 'Confira a tag: use as letras e os números exibidos no perfil do jogo.'
        else:
            try:
                player = api_get(API_URL_PLAYER + quote(tag, safe=''))
                season = player.get('bestPathOfLegendSeasonResult') or {}
                league_name = LEAGUES.get(season.get('leagueNumber'), 'Sem registro')
                wins, losses = player.get('wins', 0), player.get('losses', 0)
                winrate = round(wins / (wins + losses) * 100, 1) if wins + losses else 0
            except APIError as exc:
                error = str(exc)
    return render_template('players.html', player=player, player_tag=tag, error=error, league_name=league_name, winrate=winrate)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
