# Development Notes - Paddle Watch

**Created:** 2025-12-29
**Author:** Built with Claude Code

This document captures the research, decisions, and lessons learned during the initial build of Paddle Watch.

---

## Inspiration

The project was inspired by viewing [Windy.com's webcam interface](https://www.windy.com/-Webcams-Guntersville-Guntersville-%E2%80%BA-South-east:-Guntersville-Lake-&-Dam/webcams/1457713976):

- Split-panel layout with map on left, content on right
- Live webcam integration
- Weather data overlay on maps
- Clean, modern interface

**Goal:** Create a similar experience specifically for kayakers, with dedicated pages for different river areas.

---

## Research Phase

### Webcam Options Investigated

| Source | URL | Embed Support | Quality | Notes |
|--------|-----|---------------|---------|-------|
| **IPCamLive** | ipcamlive.com/guntersville2 | Yes (iframe) | Good | **SELECTED** - Works without auth |
| iplivecams.com | iplivecams.com/live-cams/guntersville... | No | Unknown | Aggregator, no direct embed |
| Windy Webcams API | api.windy.com/webcams | Yes (with API key) | Low (free tier) | URLs expire every 15 mins |
| Vision-Environnement | vision-environnement.com | Unknown | HD/4K | No public embed code found |
| SeeCam | see.cam | Unknown | Varies | May be stale (2yr old update) |

**Decision:** IPCamLive was chosen because:
- Public embed URL works without authentication
- Responsive iframe player
- Guntersville Lake & Dam view relevant to paddling

### Wind Map Options

| Option | Pros | Cons | Cost |
|--------|------|------|------|
| **Windy.com Embed** | Animated wind, beautiful, easy | Limited customization | FREE |
| Leaflet.js + OpenWeatherMap | Full control, custom markers | More complex, no animation | Free tier limits |
| Mapbox GL | Beautiful terrain | No wind animation | Free tier limits |
| Windy API (JS library) | Full control + animation | Complex integration | API key required |

**Decision:** Windy.com iframe embed was chosen for simplicity. Can upgrade to Leaflet.js + custom markers later if needed.

### Windy Embed URL Parameters

Discovered through testing:

```
https://embed.windy.com/embed2.html?
  lat=34.39              # Latitude
  lon=-86.16             # Longitude
  detailLat=34.39        # Detail panel lat
  detailLon=-86.16       # Detail panel lon
  zoom=11                # Zoom level (1-20)
  level=surface          # Altitude (surface, 850h, etc)
  overlay=wind           # Layer (wind, rain, temp, etc)
  product=ecmwf          # Model (ecmwf, gfs, etc)
  menu=                  # Empty = hidden
  message=true           # Show info message
  marker=true            # Show center marker
  calendar=now           # Time (now, 12h, etc)
  pressure=true          # Show pressure
  type=map               # Map type
  location=coordinates   # Location mode
  detail=true            # Show detail panel
  metricWind=mph         # Wind units
  metricTemp=%C2%B0F     # Temp units (URL encoded °F)
  radarRange=-1          # Radar range (-1 = off)
```

---

## Technical Decisions

### Why Flask?

- Simple, lightweight
- Easy to proxy API requests (avoid CORS issues)
- Jinja2 templates built-in
- Gunicorn for production WSGI

Alternatives considered:
- Pure static HTML + fetch() - Would hit CORS issues with main API
- FastAPI - Overkill for this simple app
- Node.js/Express - Could work, but Python matches main project

### Why Proxy the River API?

The main river API at `docker-blue-sound-1751.fly.dev` doesn't have CORS headers for arbitrary origins. By proxying through our Flask app:

1. Browser fetches from same origin (`paddle-watch.fly.dev/api/rivers`)
2. Flask server fetches from main API (server-to-server, no CORS)
3. Flask returns data to browser

### Glassmorphism CSS

Chose glassmorphism (frosted glass) effect for modern, premium look:

```css
background: rgba(255, 255, 255, 0.7);
backdrop-filter: blur(20px);
border: 1px solid rgba(255, 255, 255, 0.5);
box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
```

Key elements:
- Semi-transparent white background
- `backdrop-filter: blur()` for frosted effect
- Subtle white inner border
- Soft shadow

**Browser Support:** Works in all modern browsers. IE11 would show solid white (acceptable fallback).

### Color Scheme

Light mode with purple gradient background:

```css
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
```

River card accent colors:
- Short Creek: Green (#22c55e)
- South Sauty: Blue (#3b82f6)

Status colors:
- OUT: Gray (#9ca3af)
- IN: Yellow gradient (#fbbf24 → #f59e0b)
- GOOD: Green gradient (#22c55e → #16a34a)

---

## Build Process

### Step 1: Project Structure
```bash
mkdir -p /chanslor/mdc/YOUTUBE/paddle-watch/templates
```

### Step 2: Flask App (`app.py`)
- Define RIVERS dict with API paths
- Create routes for /, /api/rivers, /api/health
- Use requests library to proxy main API

### Step 3: Dashboard HTML (`templates/index.html`)
- 3-panel CSS Grid layout
- Embedded Windy.com iframe (left)
- Embedded IPCamLive iframe (upper right)
- River cards with glassmorphism (lower right)
- JavaScript fetch() every 60 seconds

### Step 4: Container Build
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
COPY templates/ templates/
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "app:app"]
```

### Step 5: Fly.io Deployment
```toml
app = 'paddle-watch'
primary_region = 'iad'  # ATL is deprecated!

[http_service]
  auto_stop_machines = 'stop'  # Save money
  min_machines_running = 0
```

---

## Issues Encountered

### Issue 1: ATL Region Deprecated

**Error:**
```
Region atl is deprecated and cannot have new resources provisioned.
```

**Solution:** Changed `primary_region` from `atl` to `iad` (Virginia).

### Issue 2: DNS Propagation Delay

After deployment, DNS took ~5 minutes to propagate. During this time:

```bash
# This failed:
curl https://paddle-watch.fly.dev/api/health

# This worked (direct IP):
curl --resolve paddle-watch.fly.dev:443:66.241.125.113 https://paddle-watch.fly.dev/api/health
```

**Lesson:** New Fly.io deployments need a few minutes for DNS. Can verify via direct IP.

### Issue 3: Shell Working Directory

Claude Code's Bash tool kept resetting to `/home/mdc`.

**Solution:** Created `deploy.sh` script that explicitly `cd`s to the project directory:
```bash
#!/bin/bash
cd /chanslor/mdc/YOUTUBE/paddle-watch
fly deploy --local-only
```

---

## Performance Notes

- **Container size:** 144 MB (Python slim base)
- **Startup time:** ~3.5 seconds
- **API response:** ~100-200ms (proxy overhead)
- **Memory usage:** ~50MB idle (Flask + Gunicorn)

---

## Future Improvements

### Short Term
- [ ] Add loading skeleton while data fetches
- [ ] Add error state UI when API fails
- [ ] Cache API responses in Flask (reduce main API load)

### Medium Term
- [x] ~~Add more rivers (tabs or dropdown selector)~~ → Done! Index page with cards
- [x] ~~Little River Canyon page~~ → Done with 6-level classification
- [ ] Replace Windy embed with Leaflet.js for custom markers
- [ ] Add put-in/take-out markers on map
- [ ] Embed sparkline charts from main API
- [ ] Add more rivers: Locust Fork, Town Creek, Mulberry Fork

### Long Term
- [ ] WebSocket for real-time updates
- [ ] Push notifications when rivers hit threshold
- [ ] PWA (Progressive Web App) for mobile
- [ ] Multiple webcam sources with selector

---

## Resources

- [Windy.com Embed Documentation](https://community.windy.com/topic/8270/windy-webcams-api)
- [IPCamLive Embed FAQ](https://www.ipcamlive.com/faqs)
- [Fly.io Documentation](https://fly.io/docs/)
- [Glassmorphism CSS Generator](https://glassmorphism.com/)
- [Main River Levels API](https://docker-blue-sound-1751.fly.dev/api)

---

## Little River Canyon Webcam Research (2025-12-29)

When adding the Little River Canyon page, we needed to find a webcam for the Fort Payne / DeKalb County area.

### Webcams Investigated

| Source | Status | Notes |
|--------|--------|-------|
| WeatherBug Mentone Traffic Cam | **401 Unauthorized** | Token-based, expires quickly |
| Cloudmont Ski Resort | **Not operational** | Page says "No webcam available" |
| Ventusky Fort Payne | **Stale** | Last image from Aug 2023 |
| IPLiveCams Alabama | **None in area** | 47 cams, all Gulf Coast/major cities |
| ALGO Traffic | **Unknown** | Requires JS, couldn't verify coverage |
| WHNT Camera Network | **Fort Payne cam down** | Not pulling fresh images |
| **WAAY 31 Albertville** | **WORKS** | Direct JPEG, ~20 miles from LRC |

### WeatherBug/TrafficLand Token Issue

Initially found a Mentone SR-193 traffic camera via WeatherBug:
```
https://ie.trafficland.com/v2.0/468476/huge?system=weatherbug-web&pubtoken=...
```

This worked briefly but returned 401 within minutes. The `pubtoken` is session-based and tied to the WeatherBug website - not suitable for embedding.

### WAAY 31 Solution

Discovered WAAY TV (local news) provides direct JPEG URLs that work without authentication:

```
https://ftp2.waaytv.com/weather/31albertville.jpg
```

**Advantages:**
- Direct JPEG URL, no tokens/auth
- Updates every ~3 minutes (max-age=200)
- 800x450 resolution
- Albertville is ~20 miles from Little River Canyon
- Multiple cameras available (Guntersville, Decatur, Muscle Shoals)

**Implementation:**
```html
<img id="weather-cam" src="https://ftp2.waaytv.com/weather/31albertville.jpg" />
<script>
  setInterval(() => {
    document.getElementById('weather-cam').src =
      'https://ftp2.waaytv.com/weather/31albertville.jpg?t=' + Date.now();
  }, 60000);
</script>
```

---

## Project Consolidation (2025-12-29)

Initially created two separate Fly.io apps:
- `paddle-watch` - South Sauty & Short Creek
- `paddle-watch-lrc` - Little River Canyon

### Why Consolidate?

1. **Cost savings** - One Fly.io app instead of two
2. **Easier maintenance** - Single codebase
3. **Better UX** - Central landing page to discover all rivers
4. **Simpler deployment** - One deploy.sh script

### Consolidation Steps

1. Destroyed `paddle-watch-lrc` Fly.io app
2. Created index landing page with river cards
3. Renamed `index.html` to `south-sauty-short-creek.html`
4. Added `little-river-canyon.html` template
5. Updated `app.py` with `RIVER_PAGES` dict and new routes
6. Added "All Rivers" back links on each river page

### New Architecture

```
paddle-watch.fly.dev/
├── /                         → Index (river cards)
├── /south-sauty-short-creek  → Guntersville dashboard
├── /little-river-canyon      → LRC dashboard
├── /api/rivers               → Short Creek + Sauty data
├── /api/river/lrc            → LRC data
└── /api/health               → Health check
```

### Adding Future Rivers

The architecture now supports easy addition of new rivers:

1. Add to `RIVER_PAGES` dict in `app.py`
2. Add Flask route
3. Create template (copy existing, update coords/webcam/API)
4. Add card to index.html
5. Deploy

---

## LRC 6-Level Classification

Little River Canyon uses a special flow classification based on expert paddler knowledge (Adam Goshorn):

| CFS Range | Status | Color | CSS Class |
|-----------|--------|-------|-----------|
| < 250 | Not Runnable | Gray | `status-not-runnable` |
| 250-400 | Good Low | Yellow | `status-good-low` |
| 400-800 | Shitty Medium | Brown | `status-shitty-medium` |
| 800-1,500 | Good Medium | Light Green | `status-good-medium` |
| 1,500-2,500 | BEST! | Green | `status-good-high` |
| > 2,500 | Too High | Red | `status-too-high` |

This is implemented in JavaScript in `little-river-canyon.html`.

---

## Commits Log

| Date | Change |
|------|--------|
| 2025-12-29 | Initial creation - Flask app, Windy embed, IPCamLive webcam, glassmorphism UI |
| 2025-12-29 | Fixed ATL region deprecation (changed to iad) |
| 2025-12-29 | Added comprehensive documentation |
| 2025-12-29 | Created paddle-watch-lrc for Little River Canyon (later consolidated) |
| 2025-12-29 | Researched LRC webcams, found WAAY 31 Albertville |
| 2025-12-29 | Consolidated into single app with index landing page |
| 2025-12-29 | Added LRC 6-level flow classification |
| 2025-12-29 | Updated all documentation |

---

*This document should be updated as the project evolves.*
