from flask import Flask, render_template, request, redirect, url_for, jsonify
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
API_BASE_URL = os.getenv('CLASH_API_BASE_URL', 'https://api.clashroyale.com').rstrip('/')
if API_BASE_URL not in {'https://api.clashroyale.com', 'https://proxy.royaleapi.dev'}:
    raise RuntimeError('CLASH_API_BASE_URL deve ser a API oficial ou o proxy RoyaleAPI.')
API_URL_CARDS = API_BASE_URL + '/v1/cards'
API_URL_PLAYER = API_BASE_URL + '/v1/players/'
API_URL_TOP = API_BASE_URL + '/v1/locations/global/pathoflegend/players?limit=3'
HEADERS = {'Authorization': f"Bearer {os.getenv('API_TOKEN')}"}
RARITIES = {'Common': 'Comum', 'Rare': 'Rara', 'Epic': 'Épica', 'Legendary': 'Lendária', 'Champion': 'Campeão'}
LEAGUES = dict(enumerate(['Mestre I', 'Mestre II', 'Mestre III', 'Campeão', 'Grande Campeão', 'Campeão Real', 'Maior Campeão'], 1))

def best_league(player):
    # Include recent progress, even before it appears in the best-season field.
    numbers = []
    for field in ('bestPathOfLegendSeasonResult', 'currentPathOfLegendSeasonResult',
                  'lastPathOfLegendSeasonResult'):
        season = player.get(field)
        number = season.get('leagueNumber') if isinstance(season, dict) else None
        # Unambiguous historical values above 7 use the former 10-league scale.
        if field == 'bestPathOfLegendSeasonResult' and type(number) is int and 8 <= number <= 10:
            number -= 3
        if type(number) is int and number in LEAGUES:
            numbers.append(number)
    return max(numbers, default=0)

def champion_results(player):
    results = []
    for field, label in (
        ('currentPathOfLegendSeasonResult', 'Temporada atual'),
        ('lastPathOfLegendSeasonResult', 'Temporada anterior'),
        ('bestPathOfLegendSeasonResult', 'Melhor temporada registrada')):
        season = player.get(field)
        if not isinstance(season, dict):
            continue
        number = season.get('leagueNumber')
        if number != 7 and not (field == 'bestPathOfLegendSeasonResult' and number == 10):
            continue
        score, rank = season.get('trophies'), season.get('rank')
        results.append({
            'label': label,
            'score': score if type(score) is int and score >= 0 else None,
            'rank': rank if type(rank) is int and rank > 0 else None,
        })
    return results

class APIError(Exception):
    pass

_cache = OrderedDict()
_cache_lock = Lock()
_fetch_locks = [Lock() for _ in range(32)]
MAX_CACHE_ENTRIES = 256

def api_get(url):
    ttl = 3600 if url == API_URL_CARDS else (300 if url == API_URL_TOP else 60)
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
        if response.status_code >= 400:
            # Only log known error identifiers, never headers, tokens or response bodies.
            reason = 'unknown'
            try:
                payload = response.json()
                candidate = payload.get('reason') if isinstance(payload, dict) else None
                if candidate in {'accessDenied', 'accessDenied.invalidIp', 'notFound',
                                 'rateLimitExceeded', 'maintenance', 'badRequest'}:
                    reason = candidate
            except ValueError:
                pass
            app.logger.warning('Clash API: HTTP %s; reason=%s; endpoint=%s; token_configured=%s',
                               response.status_code, reason,
                               'cards' if url == API_URL_CARDS else 'players',
                               bool(os.getenv('API_TOKEN', '').strip()))
            if response.status_code in (401, 403):
                raise APIError('Não foi possível autorizar a consulta ao Clash Royale. A configuração de acesso do site precisa ser verificada.')
            if response.status_code == 429:
                raise APIError('Muitas consultas no momento. Aguarde um pouco e tente novamente.')
        if response.status_code == 404:
            if url.startswith(API_URL_PLAYER):
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

@app.route('/examples/top')
def top_examples():
    try:
        data = api_get(API_URL_TOP)
        rows = []
        for item in data.get('items', [])[:3]:
            tag = item.get('tag', '')
            rank = item.get('rank')
            if not isinstance(tag, str) or not re.fullmatch(r'#[0289PYLQGRJCUV]{3,15}', tag):
                continue
            if type(rank) is not int or rank < 1:
                continue
            rows.append({'name': item.get('name', tag), 'rank': rank,
                         'url': url_for('players', tag=tag)})
        return jsonify(players=rows)
    except APIError:
        return jsonify(players=[], error='Ranking indisponível no momento.'), 503

@app.route('/players', methods=['GET', 'POST'])
def players():
    if request.method == 'POST':
        return redirect(url_for('players', tag=request.form.get('player_tag', '').strip()))
    tag = request.args.get('tag', '').strip().upper()
    player = None
    error = None
    league_name = 'Sem registro'
    league_number = 0
    winrate = 0
    if tag:
        tag = '#' + tag.lstrip('#')
        if not re.fullmatch(r'#[0289PYLQGRJCUV]{3,15}', tag):
            error = 'Confira a tag: use as letras e os números exibidos no perfil do jogo.'
        else:
            try:
                player = api_get(API_URL_PLAYER + quote(tag, safe=''))
                league_number = best_league(player)
                league_name = LEAGUES.get(league_number, 'Sem registro')
                wins, losses = player.get('wins', 0), player.get('losses', 0)
                winrate = round(wins / (wins + losses) * 100, 1) if wins + losses else 0
            except APIError as exc:
                error = str(exc)
    return render_template('players.html', player=player, player_tag=tag, error=error, league_name=league_name, league_number=league_number, winrate=winrate, champion_results=champion_results(player) if player else [])

from profile_tools import register_features
register_features(app, lambda url: api_get(url), API_URL_PLAYER, APIError, best_league, LEAGUES)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
