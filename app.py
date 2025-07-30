from flask import Flask, render_template, request, redirect, url_for
import requests
import os
from dotenv import load_dotenv
import urllib.parse

load_dotenv()
app = Flask(__name__)

API_URL_CARDS = "https://api.clashroyale.com/v1/cards"
API_URL_PLAYER = "https://api.clashroyale.com/v1/players/"
HEADERS = {
    "Authorization": f"Bearer {os.getenv('API_TOKEN')}"
}

league_names = {
    1: "Desafiante I / Challenger I",
    2: "Desafiante II / Challenger II",
    3: "Desafiante III / Challenger III",
    4: "Mestre I / Master I",
    5: "Mestre II / Master II",
    6: "Mestre III / Master III",
    7: "Campeão / Champion",
    8: "Grande Campeão / Grand Champion",
    9: "Campeão Real / Royal Champion",
    10: "Maior Campeão / Ultimate Champion"
}

# Cores para body (cor principal da liga)
body_colors = {
    1: "#643d2e",   
    2: "#503017",   
    3: "#503017",   
    4: "#c12e24",   
    5: "#534b63",   
    6: "#276b98",   
    7: "#315383",   
    8: "#ad2e4b",   
    9: "#2a6ace",   
    10: "#8d5cd2"  
}


card_colors = {
    1: "#8f4324",    
    2: "#8f969e",
    3: "#e3921d",
    4: "#fff5e1",
    5: "#adb9c5",
    6: "#d3a075",
    7: "#c13329",
    8: "#ed9d2e",
    9: "#ed9d2e",
    10: "#8198aa"   
}

card_text_colors = {
    1: "#000000",    
    2: "#131212",
    3: "#131212",
    4: "#131212",
    5: "#131212",
    6: "#131212",
    7: "#131212",
    8: "#131212",
    9: "#131212",
    10: "#131212"
}

def normalize_rarity(rarity):
    return rarity.capitalize()

def fetch_cards():
    try:
        response = requests.get(API_URL_CARDS, headers=HEADERS)
        if response.status_code == 200:
            data = response.json()
            cards = data.get("items", [])
            for card in cards:
                card["rarity"] = normalize_rarity(card.get("rarity", ""))
            return cards
        else:
            print("Erro ao acessar a API:", response.status_code)
            return []
    except Exception as e:
        print("Erro:", e)
        return []

def fetch_player(player_tag):
    try:
        encoded_tag = urllib.parse.quote(player_tag)
        response = requests.get(API_URL_PLAYER + encoded_tag, headers=HEADERS)
        if response.status_code == 200:
            return response.json()
        else:
            print("Erro ao buscar player:", response.status_code)
            return None
    except Exception as e:
        print("Erro:", e)
        return None

@app.route("/")
def index(): 


    search = request.args.get("search", "").lower()
    rarity_filter = request.args.get("rarity", "")
    sort_by = request.args.get("sort", "")

    cards = fetch_cards()

    body_color = "#98979b"

    if search:
        cards = [c for c in cards if search in c["name"].lower()]
    if rarity_filter:
        cards = [c for c in cards if c["rarity"].lower() == rarity_filter.lower()]
    if sort_by == "rarity":
        order = ["Common", "Rare", "Epic", "Legendary", "Champion"]
        cards.sort(key=lambda c: order.index(c["rarity"]))
    elif sort_by == "elixir":
        cards.sort(key=lambda c: c.get("elixirCost", 0))
    elif sort_by == "name":
        cards.sort(key=lambda c: c["name"])

    return render_template("cards.html",body_color=body_color, cards=cards, search=search, rarity=rarity_filter, sort=sort_by)

@app.route("/players", methods=["GET", "POST"])
def players():
    player_data = None
    error = None
    player_tag = ""
    league_name = None

    
    body_color = "#98979b"
    card_color = "#a8a4a6"
    card_text_color = "#000000"

    if request.method == "POST":
        player_tag = request.form.get("player_tag", "").strip()
        if player_tag:
            return redirect(url_for("players", tag=player_tag))

    if request.method == "GET":
        player_tag = request.args.get("tag", "")
        if player_tag:
            player_data = fetch_player(player_tag)
            if player_data is None:
                error = "Jogador não encontrado ou erro na API."
            else:
                league_number = player_data.get("bestPathOfLegendSeasonResult", {}).get("leagueNumber")
                league_name = league_names.get(league_number, "Desconhecida")

                # Define cores conforme liga
                if league_number in body_colors:
                    body_color = body_colors[league_number]
                if league_number in card_colors:
                    card_color = card_colors[league_number]
                if league_number in card_text_colors:
                    card_text_color = card_text_colors[league_number]

    return render_template(
        "players.html",
        player=player_data,
        error=error,
        player_tag=player_tag,
        league_name=league_name,
        body_color=body_color,
        card_color=card_color,
        card_text_color=card_text_color
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)