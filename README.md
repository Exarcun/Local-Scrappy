# Local-Scrappy

A web scraper for extracting business data from local.ch, the Swiss business directory.

## Features

- Interactive console application
- Parallel worker support (1-20 workers)
- Optional proxy rotation with hot/cold pool management
- SQLite database storage
- Excel export with business classification

## Requirements

- Python 3.10+
- Firefox browser (regular or Developer Edition)
- geckodriver

### Python Dependencies

```
selenium>=4.38.0
pandas
openpyxl
```

Install with:
```bash
pip install selenium pandas openpyxl
```

## Setup

1. **Firefox**: Install Firefox or Firefox Developer Edition

2. **geckodriver**: Download from [mozilla/geckodriver](https://github.com/mozilla/geckodriver/releases) and place in your PATH, or update the path in `src/config.py`

3. **Configuration**: Edit `src/config.py` to set your paths:
   ```python
   FIREFOX_PATH = r"C:\Program Files\Mozilla Firefox\firefox.exe"
   GECKODRIVER_PATH = r"C:\path\to\geckodriver.exe"
   ```

4. **Proxies (optional)**: Add IP-authenticated proxies to `proxies/proxylist.txt`, one per line:
   ```
   http://proxy1.example.com:8080
   http://proxy2.example.com:8080
   ```

## Usage

```bash
cd src
python main.py
```

The console will guide you through:

1. **Enter URL**: Paste a local.ch search URL (e.g., `https://www.local.ch/en/s/Zurich`)
2. **Configure**: Set pages, workers, delay, and proxy options
3. **Scrape**: Watch progress as data is extracted
4. **Export**: Optionally run export scripts to generate Excel files

## Configuration Options

| Option | Default | Description |
|--------|---------|-------------|
| Pages | 150 | Number of search result pages to scrape |
| Workers | 1 | Parallel workers (increase with proxies) |
| Max Errors | 3 | Errors before proxy swap |
| Delay | 0.3s | Delay between requests |

## Project Structure

```
Local-Scrappy/
├── src/                    # Source code
│   ├── main.py             # Entry point
│   ├── config.py           # Configuration
│   ├── db.py               # Database operations
│   ├── scraper.py          # Scraping functions
│   ├── proxy.py            # Proxy management
│   └── worker.py           # Parallel execution
├── scripts/                # Export scripts
│   ├── export_all.py       # Export all records
│   ├── export_business.py  # Export businesses only
│   └── export_uncategorized.py
├── data/                   # SQLite databases
├── proxies/                # Proxy lists
└── output/                 # Excel exports
```

## Export Scripts

Run manually or through the console menu:

```bash
python scripts/export_business.py data/yourdb.db
python scripts/export_all.py data/yourdb.db
python scripts/export_uncategorized.py data/yourdb.db
```

### Business Classification

Records are classified as businesses if they have:
- A type/category field
- A website
- A business suffix in the name (SA, AG, GmbH, Sagl, Srl, etc.)

## Data Fields

| Field | Description |
|-------|-------------|
| name | Business or person name |
| type | Business category |
| address | Street address with postal code |
| phone | Phone number |
| email | Email address |
| website | Website URL |
| source_url | Original local.ch page |

## License

MIT
