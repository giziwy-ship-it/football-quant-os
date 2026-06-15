# Coach Data Field Analysis & Storage Report
## Generated: 2026-06-13

## Current Storage Usage

| File | Size | Content |
|------|------|---------|
| worldcup_2026_full_coaches.py | 24.77 KB | 48 teams × CoachProfile (20 fields each) |
| coach_types.py | 3.43 KB | Base types (CoachProfile, CoachType, TacticalStyle) |
| coach_factor.py | 16.76 KB | CRI calculator + analysis engine |
| **TOTAL** | **~45 KB** | Complete 48-team database + engine |

## Data Field Source & Cloud Availability

### Tier 1: FIFA Official (100% authoritative, free)
| Field | Source | API/Method | Update Frequency |
|-------|--------|-----------|-----------------|
| Coach Name | FIFA Squad Lists | PDF parse | Tournament |
| Nationality | FIFA Squad Lists | PDF parse | Tournament |
| Team | FIFA Squad Lists | PDF parse | Tournament |

### Tier 2: Wikipedia/Transfermarkt (Free APIs, 95% accurate)
| Field | Source | API | Update | Space/Team |
|-------|--------|-----|--------|-----------|
| Age | Wikipedia | REST API (wikidata) | Real-time | 4 bytes |
| World Cup Experience | Wikipedia | Wiki parse | Event-based | ~50 bytes |
| Euro Experience | Wikipedia | Wiki parse | Event-based | ~50 bytes |
| Previous Teams | Transfermarkt | Web scrape | Weekly | ~100 bytes |

### Tier 3: Professional Football Data (Paid/Free APIs)
| Field | Source | API | Cost | Update | Space/Team |
|-------|--------|-----|------|--------|-----------|
| Tactical Style | Understat/FBref | REST API | Free tier | Match | ~20 bytes |
| Formation History | Transfermarkt | Web scrape | Free | Weekly | ~200 bytes |
| Avg Goals/Match | FBref | REST API | Free | Match | 8 bytes |
| Avg Conceded/Match | FBref | REST API | Free | Match | 8 bytes |

### Tier 4: Expert/Subjective (Cannot be automated)
| Field | Nature | How to Get | Reliability | Space |
|-------|--------|-----------|-------------|-------|
| Emotional Stability | Expert assessment | Football analyst ratings | 60-70% | 4 bytes |
| Media Influence | Expert assessment | Media behavior analysis | 50-60% | 4 bytes |
| Meltdown Incidents | Expert assessment | Historical event counting | 70-80% | 4 bytes |
| Rotation Tendency | Expert assessment | Lineup analysis | 75-85% | 4 bytes |
| Strategy Extremity | Expert assessment | Tactical analysis | 70-80% | 4 bytes |

## Storage Projection

### Current (Minimal)
```
48 teams × 20 fields × ~5 bytes average = ~4.8 KB raw data
+ Python overhead = ~25 KB
+ Engine code = ~17 KB
TOTAL: ~45 KB ✅
```

### With Full Cloud Sync (Historical + Real-time)
```
Base Profile (48 teams): ~5 KB
Historical Matches (per team): ~10 KB × 48 = ~480 KB
Real-time Season Data: ~20 KB × 48 = ~960 KB
Tactical Analysis Cache: ~50 KB × 48 = ~2,400 KB
Formation History: ~5 KB × 48 = ~240 KB
Player Database: ~200 KB × 48 = ~9,600 KB
TOTAL: ~13.7 MB (with full squad data)
```

### With Cloud-Only Reference (Recommended)
```
Local Cache (48 coaches): ~25 KB
Cloud API cache (match data): ~500 KB
Real-time updates: ~100 KB/day
TOTAL: ~600 KB local + cloud API on demand
```

## Cloud Data Sources Detail

### 1. Wikipedia (Free, No API Key)
```python
# Example: Get coach age
import requests

def get_coach_age_wikipedia(name):
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{name.replace(' ', '_')}"
    response = requests.get(url)
    data = response.json()
    # Extract birthdate from description or infobox
    return parse_age(data.get('description', ''))
```

### 2. Transfermarkt (Free, Web Scrape)
```python
# Coach profile: https://www.transfermarkt.com/{coach-name}/profil
# Example: https://www.transfermarkt.com/marcelo-bielsa/profil
# Data available: Age, Nationality, Current Club, Previous Clubs, 
#                 Career history, Preferred formation, Transfer history
```

### 3. FBref (Free, API Key optional)
```python
# https://fbref.com/en/coaches/
# Available: Match history, tactical stats, formations used
# Rate limit: 10 requests/minute (free tier)
```

### 4. FIFA Data Hub (Requires registration)
```python
# https://www.fifa.com/fifaplus/en/tournaments/mens/worldcup
# Official match data, squad lists, statistics
# API: https://api.fifa.com/v1/
```

## Implementation Strategy

### Option A: Full Local (Current) ✅
- **Storage**: ~45 KB
- **Pros**: Zero latency, works offline, no API costs
- **Cons**: Data stale, manual updates, subjective fields guessed
- **Best for**: Production prediction system

### Option B: Cloud Sync (Recommended for updates)
- **Storage**: ~600 KB local + cloud API
- **Pros**: Real-time data, automatic updates, historical accuracy
- **Cons**: Requires internet, API rate limits, some paid tiers
- **Best for**: Pre-tournament data refresh

### Option C: Hybrid (Best balance)
- **Storage**: ~1 MB local + cloud cache
- **Structure**:
  ```
  coaches/
  ├── base_profiles.json          # 48 teams, static (25 KB)
  ├── cloud_metadata.json         # Source references (10 KB)
  ├── match_history_cache.json    # Auto-updated (500 KB)
  └── expert_ratings.json         # Manual input (20 KB)
  ```
- **Update workflow**:
  1. FIFA PDF: Tournament data (manual, 100% accurate)
  2. Wiki/Transfermarkt: Age, history (auto, weekly)
  3. FBref: Match stats (auto, daily)
  4. Expert: Psychological fields (manual, tournament-based)

## Space Comparison

| Approach | Local Storage | Cloud Storage | Daily Transfer | API Calls/Day |
|----------|--------------|---------------|----------------|---------------|
| **Full Local** | 45 KB | 0 | 0 | 0 |
| **Cloud Sync** | 600 KB | ~500 KB | ~100 KB | ~50 |
| **Hybrid** | 1 MB | ~200 KB | ~50 KB | ~20 |
| **Full Cloud** | 100 KB (cache) | ~5 MB | ~500 KB | ~200 |

## Recommendation

**For Football Quant OS**: Keep current local approach (45 KB) + add cloud sync capability

1. **Base data**: Keep local (FIFA names + expert estimates)
2. **Auto-update**: Cloud fetch before major tournaments
3. **Cache**: Store cloud results locally to reduce API calls
4. **Expert override**: Allow manual correction of subjective fields

**Next step**: Would you like me to implement the cloud sync layer for the 4 fields that can be automated (age, WC experience, Euro experience, match history)?

---
*Report generated by Naga Core 🐉*
