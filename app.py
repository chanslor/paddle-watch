"""
Paddle Watch - Kayaking Dashboard
A beautiful experimental interface for monitoring local paddle spots
"""

import os
import requests
from flask import Flask, render_template, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Main river data API
RIVER_API_BASE = "https://docker-blue-sound-1751.fly.dev"

# River page configurations
RIVER_PAGES = {
    "south-sauty-short-creek": {
        "title": "South Sauty & Short Creek",
        "template": "south-sauty-short-creek.html",
        "rivers": {
            "short": {
                "name": "Short Creek",
                "api_path": "/api/river-levels/name/short",
                "color": "#22c55e",
            },
            "sauty": {
                "name": "South Sauty",
                "api_path": "/api/river-levels/03572690",
                "color": "#3b82f6",
            }
        }
    },
    "little-river-canyon": {
        "title": "Little River Canyon",
        "template": "little-river-canyon.html",
        "rivers": {
            "lrc": {
                "name": "Little River Canyon",
                "api_path": "/api/river-levels/02399200",
                "color": "#f59e0b",
            }
        }
    }
}


@app.route("/")
def index():
    """Serve the index/landing page with links to all river pages"""
    return render_template("index.html", pages=RIVER_PAGES)


@app.route("/south-sauty-short-creek")
def south_sauty_short_creek():
    """Serve the South Sauty & Short Creek dashboard"""
    return render_template("south-sauty-short-creek.html")


@app.route("/little-river-canyon")
def little_river_canyon():
    """Serve the Little River Canyon dashboard"""
    return render_template("little-river-canyon.html")


@app.route("/api/rivers/<page_id>")
def get_rivers_for_page(page_id):
    """Fetch river data for a specific page"""
    if page_id not in RIVER_PAGES:
        return jsonify({"error": "Page not found"}), 404

    page = RIVER_PAGES[page_id]
    results = {}

    for key, river in page["rivers"].items():
        try:
            resp = requests.get(
                f"{RIVER_API_BASE}{river['api_path']}",
                timeout=10
            )
            if resp.status_code == 200:
                results[key] = {
                    "name": river["name"],
                    "color": river["color"],
                    "data": resp.json()
                }
            else:
                results[key] = {
                    "name": river["name"],
                    "color": river["color"],
                    "error": f"API returned {resp.status_code}"
                }
        except Exception as e:
            results[key] = {
                "name": river["name"],
                "color": river["color"],
                "error": str(e)
            }

    return jsonify(results)


# Legacy endpoint for backwards compatibility
@app.route("/api/rivers")
def get_rivers():
    """Fetch river data for South Sauty & Short Creek (legacy)"""
    return get_rivers_for_page("south-sauty-short-creek")


# Single river endpoint for LRC page
@app.route("/api/river/lrc")
def get_lrc_river():
    """Fetch Little River Canyon data"""
    river = RIVER_PAGES["little-river-canyon"]["rivers"]["lrc"]
    try:
        resp = requests.get(
            f"{RIVER_API_BASE}{river['api_path']}",
            timeout=10
        )
        if resp.status_code == 200:
            return jsonify({
                "name": river["name"],
                "color": river["color"],
                "data": resp.json()
            })
        else:
            return jsonify({
                "name": river["name"],
                "color": river["color"],
                "error": f"API returned {resp.status_code}"
            })
    except Exception as e:
        return jsonify({
            "name": river["name"],
            "color": river["color"],
            "error": str(e)
        })


@app.route("/api/health")
def health():
    """Health check endpoint"""
    return jsonify({"status": "ok", "app": "paddle-watch"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
