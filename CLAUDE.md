# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with this repository.

## Project Overview

**Paddle Watch** - A collection of experimental kayaking dashboards combining live weather maps, webcams, and river data for Alabama rivers.

**Production URL:** https://paddle-watch.fly.dev/

**Related Project:** This app consumes data from the main USGS River Levels API at https://docker-blue-sound-1751.fly.dev/

## Working Directory

**Always use this directory for all commands:**
```
/chanslor/mdc/YOUTUBE/paddle-watch
```

## Quick Commands

### Deploy to Fly.io
```bash
/chanslor/mdc/YOUTUBE/paddle-watch/deploy.sh
```

### Local Development
```bash
cd /chanslor/mdc/YOUTUBE/paddle-watch
podman build -t paddle-watch:latest .
podman run -d --name paddle-watch -p 8081:8080 localhost/paddle-watch:latest
# View at http://localhost:8081
```

### Check Status
```bash
fly status -a paddle-watch
fly logs -a paddle-watch
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Fly.io: paddle-watch.fly.dev                               │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Flask App (app.py)                                   │  │
│  │                                                       │  │
│  │  Page Routes:                                         │  │
│  │  • GET /                    → Index landing page      │  │
│  │  • GET /south-sauty-short-creek → Guntersville dash   │  │
│  │  • GET /little-river-canyon → LRC dashboard           │  │
│  │                                                       │  │
│  │  API Routes:                                          │  │
│  │  • GET /api/rivers          → Short Creek + Sauty     │  │
│  │  • GET /api/river/lrc       → Little River Canyon     │  │
│  │  • GET /api/health          → Health check            │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
│  External Embeds (loaded in browser):                       │
│  • Windy.com iframe   → Wind map (per-page coordinates)    │
│  • IPCamLive iframe   → Guntersville webcam                │
│  • WAAY 31 image      → Albertville weather camera         │
└─────────────────────────────────────────────────────────────┘
              │
              ↓
┌─────────────────────────────────────────────────────────────┐
│  Main API: docker-blue-sound-1751.fly.dev                   │
│                                                             │
│  • /api/river-levels/name/short  → Short Creek data        │
│  • /api/river-levels/03572690    → South Sauty data        │
│  • /api/river-levels/02399200    → Little River Canyon     │
└─────────────────────────────────────────────────────────────┘
```

## File Structure

| File | Purpose |
|------|---------|
| `app.py` | Flask application with page routes and API proxy |
| `templates/index.html` | Landing page with river cards |
| `templates/south-sauty-short-creek.html` | Guntersville dashboard |
| `templates/little-river-canyon.html` | LRC dashboard with 6-level guide |
| `requirements.txt` | Python dependencies |
| `fly.toml` | Fly.io deployment config |
| `Containerfile` | Docker/Podman build |
| `deploy.sh` | One-command deployment |

## River Pages

### South Sauty & Short Creek (`/south-sauty-short-creek`)
- **Map**: Centered on 34.39, -86.16
- **Webcam**: IPCamLive Guntersville (iframe)
- **API**: `/api/rivers`

### Little River Canyon (`/little-river-canyon`)
- **Map**: Centered on 34.37, -85.63
- **Webcam**: WAAY 31 Albertville (auto-refresh image)
- **API**: `/api/river/lrc`
- **Special**: 6-level flow classification

## Webcam Sources

### IPCamLive - Guntersville
```
https://www.ipcamlive.com/player/player.php?alias=guntersville2&autoplay=1
```

### WAAY 31 Cameras (direct JPEG, refresh with cache-buster)
| Location | URL |
|----------|-----|
| Albertville | `https://ftp2.waaytv.com/weather/31albertville.jpg` |
| Guntersville | `https://ftp2.waaytv.com/weather/31guntersville.jpg` |
| Decatur | `https://ftp2.waaytv.com/weather/31decatur.jpg` |
| Muscle Shoals | `https://ftp2.waaytv.com/weather/31shoals.jpg` |

## Adding a New River Page

1. **Add to `RIVER_PAGES` in `app.py`**:
```python
"new-river": {
    "title": "New River",
    "template": "new-river.html",
    "rivers": {
        "key": {
            "name": "River Name",
            "api_path": "/api/river-levels/SITE_ID",
            "color": "#hexcolor",
        }
    }
}
```

2. **Add Flask route**:
```python
@app.route("/new-river")
def new_river():
    return render_template("new-river.html")
```

3. **Create template** (`templates/new-river.html`):
   - Copy existing template
   - Update Windy.com coordinates
   - Update webcam source
   - Update API endpoint in JavaScript

4. **Add card to `templates/index.html`**

5. **Deploy**: `/chanslor/mdc/YOUTUBE/paddle-watch/deploy.sh`

## LRC 6-Level Classification

| CFS | Status | CSS Class |
|-----|--------|-----------|
| < 250 | Not Runnable | `status-not-runnable` |
| 250-400 | Good Low | `status-good-low` |
| 400-800 | Shitty Medium | `status-shitty-medium` |
| 800-1,500 | Good Medium | `status-good-medium` |
| 1,500-2,500 | BEST! | `status-good-high` |
| > 2,500 | Too High | `status-too-high` |

## Deployment Notes

- **Region:** iad (Virginia) - ATL is deprecated
- **Auto-stop:** Machines stop when idle to save costs
- **Image size:** ~144 MB

## Troubleshooting

### Webcam not loading
- IPCamLive: Check [ipcamlive.com/guntersville2](https://www.ipcamlive.com/guntersville2)
- WAAY 31: Direct JPEG, should always work

### River data not updating
- Check main API: https://docker-blue-sound-1751.fly.dev/api/health
- View logs: `fly logs -a paddle-watch`

### DNS not resolving (new deploy)
```bash
curl --resolve paddle-watch.fly.dev:443:66.241.125.113 https://paddle-watch.fly.dev/api/health
```

---

*Created: 2025-12-29*
*Last Updated: 2025-12-29*
