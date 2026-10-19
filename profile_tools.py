"""Profile tools. Extra API requests only happen on explicit navigation."""
from datetime import datetime, timezone
from urllib.parse import urlencode, quote
import re
from flask import request, render_template

TAG_PATTERN = r'#[0289PYLQGRJCUV]{3,15}'

def normalize_tag(value):
    tag = '#' + value.strip().upper().lstrip('#')
    return tag if re.fullmatch(TAG_PATTERN, tag) else None

def deck_info(cards):
    cards = [c for c in (cards or []) if isinstance(c, dict)]
    ids = [c.get('id') for c in cards]
    valid = len(ids) == 8 and len(set(str(i) for i in ids)) == 8 and all(type(i) is int and 26000000 <= i < 29000000 for i in ids)
    costs = [c.get('elixirCost') for c in cards]
    average = round(sum(costs) / 8, 1) if len(costs) == 8 and all(type(c) in (int, float) and c >= 0 for c in costs) else None
    link = 'https://link.clashroyale.com/deck/en?' + urlencode({'deck': ';'.join(map(str, ids))}) if valid else None
    return {'cards': cards, 'link': link, 'average': average}

def battle_rows(data, tag):
    rows = []
    for battle in data[:10] if isinstance(data, list) else []:
        team = [p for p in (battle.get('team') or []) if isinstance(p, dict)]
        opponents = [p for p in (battle.get('opponent') or []) if isinstance(p, dict)]
        own = next((p for p in team if p.get('tag') == tag), None)
        if own is None or not opponents:
            continue
        a, b = own.get('crowns'), opponents[0].get('crowns')
        result, style = 'Resultado não informado', 'unknown'
        # Multi-player modes and equal crowns are not enough to infer a winner.
        if len(team) == len(opponents) == 1 and type(a) is int and type(b) is int:
            if a > b: result, style = 'Vitória', 'win'
            elif a < b: result, style = 'Derrota', 'loss'
            else: result, style = 'Empate ou desempate não informado', 'draw'
        timestamp = None
        try:
            timestamp = datetime.strptime(battle.get('battleTime', ''), '%Y%m%dT%H%M%S.%fZ').replace(tzinfo=timezone.utc).isoformat()
        except (ValueError, TypeError):
            pass
        rows.append({'result': result, 'style': style, 'crowns': f'{a} × {b}' if type(a) is int and type(b) is int else '—',
                     'mode': (battle.get('gameMode') or {}).get('name') or battle.get('type', 'Batalha'),
                     'timestamp': timestamp, 'team': team, 'opponents': opponents,
                     'deck': deck_info(own.get('cards')), 'opponent_decks': [dict(name=p.get('name', 'Adversário'), deck=deck_info(p.get('cards'))) for p in opponents]})
    return rows

def comparison(player, best_league, leagues):
    wins, losses = player.get('wins', 0), player.get('losses', 0)
    current = player.get('currentPathOfLegendSeasonResult') or {}
    last = player.get('lastPathOfLegendSeasonResult') or {}
    def points(season):
        value = season.get('trophies')
        return value if season.get('leagueNumber') == 7 and type(value) is int and value >= 0 else '—'
    rank = current.get('rank')
    return {'name': player.get('name', ''), 'tag': player.get('tag', ''), 'values': [
        leagues.get(best_league(player), 'Sem registro'),
        leagues.get(current.get('leagueNumber'), 'Sem registro'),
        points(current), points(last), f'#{rank}' if type(rank) is int and rank > 0 else 'Não informado',
        player.get('trophies', '—'), player.get('bestTrophies', '—'), wins, losses,
        f'{round(wins / (wins + losses) * 100, 1)}%' if wins + losses else '—',
        (player.get('clan') or {}).get('name', 'Sem clã')], 'deck': deck_info(player.get('currentDeck'))}

def register_features(app, api_get, player_url, api_error, best_league, leagues):
    app.jinja_env.globals['deck_info'] = deck_info

    @app.route('/compare')
    def compare():
        inputs = [request.args.get('a', '').strip(), request.args.get('b', '').strip()]
        profiles, errors = [], []
        if any(inputs):
            for i, raw in enumerate(inputs):
                tag = normalize_tag(raw)
                if not tag:
                    profiles.append(None); errors.append(f'Confira a tag do jogador {i + 1}.'); continue
                try:
                    profiles.append(comparison(api_get(player_url + quote(tag, safe='')), best_league, leagues)); errors.append(None)
                except api_error as exc:
                    profiles.append(None); errors.append(str(exc))
        labels = ['Melhor liga registrada', 'Liga atual', 'Pontos · temporada atual (Maior Campeão)', 'Pontos · temporada anterior (Maior Campeão)', 'Ranking global · temporada atual', 'Troféus', 'Recorde de troféus', 'Vitórias', 'Derrotas', 'Taxa de vitória', 'Clã']
        return render_template('compare.html', inputs=inputs, profiles=profiles, errors=errors, labels=labels)

    @app.route('/battles')
    def battles():
        raw = request.args.get('tag', '')
        tag, rows, error = normalize_tag(raw), [], None
        if not tag:
            error = 'Confira a tag do jogador.'
        else:
            try:
                rows = battle_rows(api_get(player_url + quote(tag, safe='') + '/battlelog'), tag)
            except api_error as exc:
                error = str(exc)
        return render_template('battles.html', tag=tag or raw, battles=rows, error=error)
