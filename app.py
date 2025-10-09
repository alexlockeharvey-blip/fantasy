from flask import Flask, render_template, jsonify, redirect, url_for
import requests

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True

# League configuration
LEAGUES = {
    "league1": {
        "id": "1268779385725390848",
        "name": "W.A.G.S. Dashboard",
        "teams": {
            "Browns": ["pitonthefield", "anthonybrown53"],
            "Wilsons": ["bellyconklin", "JacksonWilson54"],
            "MD+PA": ["TheVester", "clairebear000"],
            "MD+PHD": ["nkbryson", "sammyslay1129"]
        },
        "show_teams": True
    },
    "league2": {  # Bookkeepers League
        "id": "1216902891705466880",
        "name": "Bookkeepers Dashboard",
        "teams": {},
        "show_teams": False
    }
}

# Root redirects to home
@app.route("/")
def root():
    return redirect(url_for("landing_page"))

# Home page
@app.route("/home")
def landing_page():
    return render_template("home.html", league_key="home")

# Fetch league data
def fetch_data(league_key):
    league = LEAGUES[league_key]
    league_id = league["id"]
    teams_dict = league.get("teams", {})
    show_teams = league.get("show_teams", False)

    # Get league users
    users = requests.get(f"https://api.sleeper.app/v1/league/{league_id}/users").json()
    user_map = {u["user_id"]: u["display_name"] for u in users}
    user_map_inv = {v: k for k, v in user_map.items()}

    # Get league rosters
    rosters = requests.get(f"https://api.sleeper.app/v1/league/{league_id}/rosters").json()
    roster_map = {str(r["owner_id"]): r for r in rosters if r.get("owner_id")}

    # Individual standings
    individual_standings = []
    for user_id, name in user_map.items():
        r = roster_map.get(str(user_id))
        wins = r.get("settings", {}).get("wins", 0) if r else 0
        losses = r.get("settings", {}).get("losses", 0) if r else 0
        points = r.get("settings", {}).get("fpts", 0) if r else 0
        individual_standings.append({"name": name, "wins": wins, "losses": losses, "points": points})
    individual_standings.sort(key=lambda x: (-x["wins"], -x["points"]))

    # Team standings
    team_standings = []
    if show_teams:
        for team_name, players in teams_dict.items():
            team_wins = team_losses = team_points = 0
            for p in players:
                owner_id = user_map_inv.get(p)
                if owner_id and str(owner_id) in roster_map:
                    r = roster_map[str(owner_id)]
                    team_wins += r.get("settings", {}).get("wins", 0)
                    team_losses += r.get("settings", {}).get("losses", 0)
                    team_points += r.get("settings", {}).get("fpts", 0)
            team_standings.append({
                "team_name": team_name,
                "players": players,
                "wins": team_wins,
                "losses": team_losses,
                "points": team_points
            })
        team_standings.sort(key=lambda x: (-x["wins"], -x["points"]))

    return individual_standings, team_standings, show_teams

# Get last completed week
def get_last_completed_week(league_id):
    # First get league info to determine sport and season
    league_info = requests.get(f"https://api.sleeper.app/v1/league/{league_id}").json()
    season = league_info.get("season")
    sport = league_info.get("sport", "nfl")

    # Then get current state for that sport/season
    state_info = requests.get(f"https://api.sleeper.app/v1/state/{sport}").json()
    current_week = state_info.get("week")

    # Return the previous week (or week 1 if current_week is None/1)
    return max((current_week or 1) - 1, 1)


# Get highest and lowest scorer for a week
def get_week_top_and_bottom_scorers(league_id, week):
    matchups = requests.get(f"https://api.sleeper.app/v1/league/{league_id}/matchups/{week}").json()

    lowest_player = None
    lowest_points = float("inf")
    highest_player = None
    highest_points = float("-inf")

    for matchup in matchups:
        roster_id = matchup.get("roster_id")
        points = matchup.get("points", 0.0)
        if roster_id is None:
            continue

        if points < lowest_points:
            lowest_points = points
            lowest_player = roster_id
        if points > highest_points:
            highest_points = points
            highest_player = roster_id

    # Map roster_id → owner_id
    rosters = requests.get(f"https://api.sleeper.app/v1/league/{league_id}/rosters").json()
    roster_map = {r["roster_id"]: r for r in rosters if r.get("roster_id")}

    # Map user_id → display_name
    users = requests.get(f"https://api.sleeper.app/v1/league/{league_id}/users").json()
    user_map = {u["user_id"]: u["display_name"] for u in users}

    lowest_name = "Unknown"
    highest_name = "Unknown"
    if lowest_player in roster_map:
        owner_id = roster_map[lowest_player].get("owner_id")
        lowest_name = user_map.get(owner_id, "Unknown")
    if highest_player in roster_map:
        owner_id = roster_map[highest_player].get("owner_id")
        highest_name = user_map.get(owner_id, "Unknown")

    return {
        "lowest": {"player": lowest_name, "points": lowest_points},
        "highest": {"player": highest_name, "points": highest_points}
    }

# League pages
@app.route("/<league_key>")
def league_page(league_key):
    if league_key not in LEAGUES:
        return "League not found", 404

    individual, team, show_teams = fetch_data(league_key)
    league_name = LEAGUES[league_key]["name"]

    top_bottom = None
    last_week = None
    if league_key == "league2":  # Bookkeepers
        league_id = LEAGUES[league_key]["id"]
        last_week = get_last_completed_week(league_id)
        top_bottom = get_week_top_and_bottom_scorers(league_id, last_week)

    return render_template(
        "index.html",
        individual_standings=individual,
        team_standings=team,
        show_teams=show_teams,
        league_key=league_key,
        league_name=league_name,
        top_bottom=top_bottom,
        last_week=last_week
    )

#Bookeeper subpages
# @app.route("/bookkeepers/rules")
# def bookkeepers_rule():
#     return render_template("rules.html")
# @app.route("/bookkeepers/poll")
# def bookkeepers_poll():
#     return render_template("bookkeepers_poll.html")
# @app.route("/bookkeepers/stats")
# def bookkeepers_stats():
#     return render_template("bookkeepers_stats.html")
# @app.route("/bookkeepers/players")
# def bookkeepers_players():
#     return render_template("bookkeepers_players.html")
@app.route("/bookkeepers/incomplete")
def incomplete():
    return render_template("incomplete.html")
# API endpoint
@app.route("/api/<league_key>")
def api_standings(league_key):
    if league_key not in LEAGUES:
        return jsonify({"error": "League not found"}), 404
    individual, team, show_teams = fetch_data(league_key)
    return jsonify({
        "individual_standings": individual,
        "team_standings": team,
        "show_teams": show_teams
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
