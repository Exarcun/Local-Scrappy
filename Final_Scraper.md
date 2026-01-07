# local.ch Scraper - Final Documentation

## Project Overview

A production-ready web scraping system for extracting business data from local.ch, the Swiss business directory. The system evolved from a simple proof-of-concept into a fully-featured console application with parallel processing, proxy rotation, and modular post-processing scripts.

---

## Evolution Timeline

### Phase 1: Proof of Concept

**Objective:** Verify that local.ch can be scraped with Selenium and Firefox.

**Initial Setup:**
- Python 3.12 + Selenium 4.38
- Firefox Developer Edition with geckodriver
- Basic link extraction from search results

**First Script:** `scraper_localch.py`
- Single-threaded execution
- Hardcoded target URL (Mesolcina region)
- JSON output for extracted links
- Basic business detail extraction

**Challenges Identified:**
- CSS selectors needed refinement (name field captured ratings, type showed cookie banners)
- No persistent storage
- Slow execution (one page at a time)

---

### Phase 2: Data Refinement

**Objective:** Improve data quality with better selectors.

**Selector Evolution:**

| Field | Initial Selector | Final Selector | Reason |
|-------|------------------|----------------|--------|
| Name | `.kY` | `h1` | Was capturing ratings text |
| Type | `.kK` | `h2` (filtered) | Cookie consent interference |
| Phone | nth-child | `a[href^='tel:']` | Semantic, reliable |
| Email | nth-child | `a[href^='mailto:']` | Semantic, reliable |
| Address | `.tn` | `button` with regex `\d{4}` | Postal code pattern |
| Website | - | `a[data-testid='contact-link']` | Added later |

**Website Field Discovery:**
- Initially overlooked in data model
- Required filtering: exclude `local.ch`, `wa.me`, `tel:`, `mailto:`

---

### Phase 3: SQLite Integration

**Objective:** Persistent storage with duplicate handling.

**Implementation:**
- SQLite database with UNIQUE constraint on `source_url`
- `INSERT OR IGNORE` for safe duplicate handling
- Automatic schema creation on startup

**Schema:**
```sql
CREATE TABLE businesses (
    id INTEGER PRIMARY KEY,
    name TEXT,
    type TEXT,
    address TEXT,
    phone TEXT,
    email TEXT,
    website TEXT,
    source_url TEXT UNIQUE,
    scraped_at TEXT,
    created_at DEFAULT CURRENT_TIMESTAMP
)
```

---

### Phase 4: Parallel Processing

**Objective:** Dramatically improve scraping speed.

**Implementation:** `scraper_parallel.py`
- `ThreadPoolExecutor` with 10 workers
- Thread-safe SQLite writes via `threading.Lock()`
- Links divided evenly among workers
- ~10x speed improvement

**Proxy Integration:**
- 100 residential proxies (IP-authenticated)
- Each worker assigned unique proxy
- Avoided rate limiting from local.ch

---

### Phase 5: Proxy Hot/Cold Rotation

**Objective:** Handle network failures gracefully.

**Problem:** Proxies occasionally fail, causing worker timeouts and lost progress.

**Solution:** `ProxyPool` class with hot/cold management

```
COLD PROXIES ──────────────────> ASSIGNED TO WORKER
     ^                                  │
     │                                  │ 3+ errors
     │                                  v
     └──── 5 min cooldown ───── HOT PROXIES
```

**Features:**
- Automatic proxy swap after 3 consecutive errors
- 5-minute cooldown before hot proxy returns to cold pool
- Failed URLs retried with new proxy (no data loss)
- Real-time status: "Proxies: 92 cold, 8 hot"

---

### Phase 6: Data Export & Classification

**Objective:** Separate businesses from private entries.

**Classification Logic:**
```
IS_BUSINESS if ANY:
  - has type field populated
  - has website
  - name contains: SA, Sagl, AG, GmbH, Srl, Snc, & Co
```

**Results (Mesolcina region):**
- Total records: 2,795
- Businesses: 963
- Uncategorized: 1,832

**Export Format:** Excel (.xlsx) with auto-width columns

---

### Phase 7: Consolidated Console Application

**Objective:** Single entry point for all functionality.

**Problems with POC approach:**
- Multiple scripts to run manually
- Hardcoded configuration
- No flexibility for different regions
- Two-pass scraping (details + websites separate)

**Solution:** Interactive console application

```
┌─────────────────────────────────────────────────────────┐
│  local.ch Scraper v1.0                                  │
├─────────────────────────────────────────────────────────┤
│  Step 1: Enter base URL                                 │
│  > https://www.local.ch/it/s/Ticino?rid=xxx             │
│                                                         │
│  Step 2: Configuration                                  │
│  > Pages to scrape [150]:                               │
│  > Use proxies? (y/n) [Y/n]:                            │
│  > Number of workers [8]:                               │
│  > Max errors before proxy swap [3]:                    │
│  > Delay between requests (sec) [0.3]:                  │
│                                                         │
│  Step 3-4: Scraping with progress                       │
│  Step 5: Optional post-processing scripts               │
└─────────────────────────────────────────────────────────┘
```

**Key Improvements:**
| POC | Console App |
|-----|-------------|
| Hardcoded URL | User input |
| Fixed DB name | Derived from URL (`ticino.db`) |
| 2-pass scraping | Single pass (all data) |
| Proxies required | Proxies optional |
| Manual exports | Menu-driven scripts |
| Files everywhere | Organized folders |

---

## Final Architecture

```
infra-scraper/
├── src/                    # Source code
│   ├── main.py             # Console entry point
│   ├── config.py           # Configuration constants
│   ├── db.py               # Database operations
│   ├── scraper.py          # Core scraping functions
│   ├── proxy.py            # ProxyPool class
│   └── worker.py           # Parallel execution
├── scripts/                # Post-processing
│   ├── export_all.py
│   ├── export_business.py
│   └── export_uncategorized.py
├── data/                   # SQLite databases
├── proxies/                # Proxy lists
└── output/                 # Excel exports
```

---

## Module Responsibilities

### `config.py`
- Path constants (Firefox, geckodriver, directories)
- Default parameters (pages, workers, delays)
- Business classification suffixes

### `db.py`
- Schema initialization
- Thread-safe insert operations
- Statistics queries

### `scraper.py`
- WebDriver initialization (with/without proxy)
- Link extraction from search results
- Business data extraction (all fields in one visit)

### `proxy.py`
- Proxy file loading
- `ProxyPool` class with hot/cold rotation
- Thread-safe proxy assignment

### `worker.py`
- Link distribution among workers
- Worker function with error handling
- `ThreadPoolExecutor` orchestration

### `main.py`
- Interactive prompts
- Configuration validation
- Execution flow control
- Script runner

---

## Usage

### Basic Run
```bash
cd src
python main.py
```

### Without Proxies
Remove or rename `proxies/proxylist.txt`. The app will detect this and run with a single worker using direct connection.

### Custom Scripts
Add `.py` files to `scripts/` folder. They receive the database path as argument:
```bash
python scripts/export_business.py data/ticino.db
```

---

## Configuration Options

| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| Pages | 150 | 1+ | Search result pages to scrape |
| Workers (with proxy) | 8 | 1-20 | Parallel workers (user's choice) |
| Workers (no proxy) | 1 | 1-3 | Limited to avoid rate limiting |
| Max Errors | 3 | 1+ | Errors before proxy swap |
| Delay | 0.3s | 0+ | Between requests |
| Proxy Cooldown | 300s | 60+ | Hot proxy recovery time |

**Note:** Worker count is fully customizable. Use fewer workers (2-4) for stability, more (8-20) for speed when you have enough proxies.

---

## Data Flow

```
User Input (URL)
      │
      v
Link Extraction ──────> [2,822 links]
      │
      v
Parallel Scraping ────> [8 workers, proxy rotation]
      │
      v
SQLite Database ──────> data/region.db
      │
      v
Export Scripts ───────> output/region_businesses.xlsx
```

---

## Performance Metrics (Mesolcina Region)

| Metric | Value |
|--------|-------|
| Total pages | 150 |
| Links extracted | 2,822 |
| Records saved | 2,795 |
| With email | ~2,750 |
| With website | 243 |
| Classified as business | 963 |

---

## Future Enhancements

1. **Resume capability** - Continue interrupted scrapes
2. **Scheduling** - Periodic re-scraping for updates
3. **Additional regions** - Batch processing multiple URLs
4. **Data validation** - Phone/email format verification
5. **API export** - JSON/CSV output options

---

## Dependencies

```
selenium>=4.38.0
pandas
openpyxl
```

**Browser:** Firefox Developer Edition
**Driver:** geckodriver 0.36.0 (auto-managed via webdriver-manager cache)

---

*Documentation created: January 7, 2026*
