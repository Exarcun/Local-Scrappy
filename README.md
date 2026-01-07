<div align="center">

# 🦎 Local-Scrappy

**A powerful web scraper for Swiss business data**

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Selenium](https://img.shields.io/badge/Selenium-4.38+-43B02A?style=for-the-badge&logo=selenium&logoColor=white)](https://selenium.dev)
[![Firefox](https://img.shields.io/badge/Firefox-Browser-FF7139?style=for-the-badge&logo=firefox&logoColor=white)](https://mozilla.org/firefox)
[![SQLite](https://img.shields.io/badge/SQLite-Database-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://sqlite.org)

Extract business data from [local.ch](https://local.ch), the Swiss business directory.

---

</div>

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🖥️ **Interactive Console** | Guided setup with prompts for all options |
| ⚡ **Parallel Workers** | Scale from 1 to 20 concurrent workers |
| 🔄 **Proxy Rotation** | Hot/cold pool with automatic recovery |
| 💾 **SQLite Storage** | Persistent database per region |
| 📊 **Excel Export** | Business classification & filtering |

---

## 📦 Requirements

### System
- 🐍 Python 3.10+
- 🦊 Firefox (regular or Developer Edition)
- 🔧 geckodriver

### Dependencies

```bash
pip install selenium pandas openpyxl
```

---

## 🚀 Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/Exarcun/Local-Scrappy.git
cd Local-Scrappy
pip install selenium pandas openpyxl
```

### 2. Configure

Edit `src/config.py` with your paths:

```python
FIREFOX_PATH = r"C:\Program Files\Mozilla Firefox\firefox.exe"
GECKODRIVER_PATH = r"C:\path\to\geckodriver.exe"
```

### 3. Run

```bash
cd src
python main.py
```

---

## 🎮 Usage

The interactive console guides you through:

```
┌─────────────────────────────────────────────────────────┐
│  🦎 Local-Scrappy v1.0                                  │
├─────────────────────────────────────────────────────────┤
│  1️⃣  Enter local.ch search URL                          │
│  2️⃣  Configure pages, workers, delay                    │
│  3️⃣  Watch scraping progress                            │
│  4️⃣  Export to Excel                                    │
└─────────────────────────────────────────────────────────┘
```

---

## ⚙️ Configuration

| Option | Default | Description |
|:------:|:-------:|-------------|
| 📄 Pages | `150` | Search result pages to scrape |
| 👷 Workers | `1` | Parallel workers (1-20) |
| ❌ Max Errors | `3` | Errors before proxy swap |
| ⏱️ Delay | `0.3s` | Delay between requests |

---

## 📁 Project Structure

```
Local-Scrappy/
├── 📂 src/                     # Source code
│   ├── main.py                 # Entry point
│   ├── config.py               # Configuration
│   ├── db.py                   # Database operations
│   ├── scraper.py              # Scraping functions
│   ├── proxy.py                # Proxy management
│   └── worker.py               # Parallel execution
├── 📂 scripts/                 # Export scripts
│   ├── export_all.py
│   ├── export_business.py
│   └── export_uncategorized.py
├── 📂 data/                    # SQLite databases
├── 📂 proxies/                 # Proxy lists
└── 📂 output/                  # Excel exports
```

---

## 📊 Data Fields

| Field | Description |
|-------|-------------|
| `name` | Business or person name |
| `type` | Business category |
| `address` | Street address with postal code |
| `phone` | Phone number |
| `email` | Email address |
| `website` | Website URL |
| `source_url` | Original local.ch page |

---

## 🔀 Proxy Support (Optional)

Add IP-authenticated proxies to `proxies/proxylist.txt`:

```
http://proxy1.example.com:8080
http://proxy2.example.com:8080
```

The system uses **hot/cold pool rotation**:
- ❄️ **Cold proxies**: Available for use
- 🔥 **Hot proxies**: Failed, cooling down (5 min)
- 🔄 Auto-swap after 3 consecutive errors

---

## 📤 Export Scripts

Run through the console menu or manually:

```bash
# Export businesses only
python scripts/export_business.py data/yourdb.db

# Export all records
python scripts/export_all.py data/yourdb.db

# Export uncategorized
python scripts/export_uncategorized.py data/yourdb.db
```

### Business Classification

Records are classified as **businesses** if they have:
- ✅ A type/category field
- ✅ A website
- ✅ Business suffix (SA, AG, GmbH, Sagl, Srl, etc.)

---

## 📄 License

MIT

---

<div align="center">

**Made with 🦎 by [Exarcun](https://github.com/Exarcun)**

</div>
