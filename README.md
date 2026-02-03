# DealBot

**Production-ready macOS app for parsing, validating, and publishing Amazon deals to WhatsApp.**

Built with Toga (BeeWare), Briefcase packaging, Amazon PA-API validation, Bitly/Cloudflare short links, Whapi publishing, and SQLite analytics.

---

## Features

- 📄 **TXT File Parser** - Parse deal records from text files
- 💰 **Amazon PA-API Validation** - Real-time price validation via Product Advertising API
- 🔧 **Configurable Price Adjustment** - Apply custom formulas (multiplier + additive)
- 🔗 **Short Links** - Bitly branded domain (amzon.fyi) or Cloudflare Workers fallback
- 🎨 **Interstitial Pages** - Beautiful countdown landing pages before redirect
- ⭐ **Ratings Integration** - Keepa, Rainforest, or SerpAPI (optional)
- 📱 **WhatsApp Publishing** - Via Whapi.cloud to channels & groups
- 💾 **SQLite Database** - Complete analytics and audit trail
- 🖥️ **Native macOS GUI** - Toga-based, installs as .app, launches from Launchpad

---

## Quick Start

### Installation

1. **Install Python 3.11+**
   ```bash
   brew install python@3.11
   ```

2. **Clone & Setup**
   ```bash
   cd /Users/m4owen/01.\ Apps/07.\ Windsurf/03.\ Claude/DealBot
   make setup
   ```

3. **Configure Environment**
   ```bash
   cp .env.example .env
   ```

   Edit `.env` and add:
   ```bash
   WHAPI_API_KEY=your_whapi_key
   AMAZON_PAAPI_ACCESS_KEY=AKPA8WCRLR1761407306
   AMAZON_PAAPI_SECRET_KEY=your_secret_key
   AMAZON_ASSOCIATE_TAG=your_tag-21
   BITLY_TOKEN=your_bitly_token  # Optional: for branded short links
   KEEPA_API_KEY=your_keepa_key  # Optional: for ratings
   ```

4. **Customize Configuration**

   Edit `config.yaml` to adjust:
   - Default source directory
   - Price adjustment formula
   - WhatsApp recipients
   - Short link provider
   - Ratings provider

---

## Usage

### Run in Development

```bash
make run
```

### Package as macOS .app

```bash
make package
```

This creates `DealBot.app` in the `build/` directory. Double-click to install, then launch from Launchpad.

### Workflow

1. **Select TXT File** - Click "Select TXT File" button or use ⌘O
2. **Review Deals** - Parsed deals appear in table with validation status
3. **Configure Options** - Toggle "Send to Group" if needed
4. **Publish** - Click "Process & Publish Selected"
5. **Monitor** - View status log for progress and errors

---

## Configuration

### Price Adjustment

In `config.yaml`:

```yaml
price_adjustment:
  multiplier: 1.00  # FinalPrice = ValidatedPrice * multiplier + additive
  additive: 0.00
```

Examples:
- **10% markup**: `multiplier: 1.10, additive: 0.00`
- **Flat fee**: `multiplier: 1.00, additive: 5.00`
- **Combined**: `multiplier: 1.05, additive: 2.00`

### WhatsApp Recipients

```yaml
whatsapp:
  recipients:
    channel: "0029Vb6PJDh6WaKjaAcWAX1h@broadcast"
    group: "120363269876975950@g.us"
  send_to_group: false  # Toggle in GUI or set default here
```

### Short Links

**Option A: Bitly (Recommended)**

1. Create Bitly account at https://bitly.com
2. Add custom domain `amzon.fyi` to your Bitly account
3. Get API token from https://app.bitly.com/settings/api/
4. Set `BITLY_TOKEN` in `.env`

**Option B: Cloudflare Workers (Fallback)**

See `workers/README.md` for deployment instructions.

### Ratings Providers

Set in `config.yaml`:

```yaml
ratings:
  enabled: true
  provider: "keepa"  # "keepa" | "rainforest" | "serpapi"
```

Add corresponding API key to `.env`.

---

## TXT File Format

Example `deals.txt`:

```
Amazing Product ES
https://amazon.es/dp/B08N5WRWNW
€49.99

Another Great Deal EN
https://amazon.co.uk/dp/B08ABCDEFG?tag=existing-21
£39.99
```

**Requirements:**
- Each deal on separate line or block
- Amazon URL with ASIN
- Optional: stated price with currency symbol
- Optional: language flag (ES/EN)

---

## Troubleshooting

### PA-API Errors

**403 Forbidden**
- Check `AMAZON_PAAPI_SECRET_KEY` is correct
- Verify your PA-API account is active
- Ensure you've made at least 3 sales in last 180 days (PA-API requirement)

**Throttling (429)**
- PA-API has rate limits (1 request/second)
- App includes retry logic with exponential backoff

### Whapi Errors

**401 Unauthorized**
- Verify `WHAPI_API_KEY` in `.env`
- Check key hasn't expired

**429 Rate Limit**
- Whapi has rate limits per channel
- App includes retry logic

### Bitly Errors

**403 Forbidden**
- Check `BITLY_TOKEN` is valid
- Verify custom domain `amzon.fyi` is connected to your account

### Price Discrepancy Warnings

If stated price differs from validated price by >15%, deal is marked "needs_review". Adjust threshold in `config.yaml`:

```yaml
price_validation:
  discrepancy_threshold: 0.15  # 15%
```

---

## Development

### Run Tests

```bash
make test
```

### Lint & Format

```bash
make lint
make format
```

### Database

SQLite database: `dealbot.db`

**Open in GUI**: Tools → Open Database

**Export to CSV**: File → Export to CSV

---

## Architecture

```
adp/
├── app.py              # Toga GUI application
├── controller.py       # Pipeline orchestration
├── models.py           # Pydantic data models
├── parsers/
│   └── txt_parser.py   # TXT file parsing
├── services/
│   ├── amazon_paapi.py # Price validation
│   ├── affiliates.py   # Tag management
│   ├── pricing.py      # Price adjustment
│   ├── shortlinks.py   # Bitly/Cloudflare
│   ├── interstitial.py # FastAPI server
│   ├── ratings.py      # Keepa/Rainforest/SerpAPI
│   └── whapi.py        # WhatsApp publishing
├── storage/
│   └── db.py           # SQLite wrapper
├── ui/
│   ├── templates/
│   │   └── interstitial.html.j2
│   └── whatsapp_format.py
└── utils/
    ├── config.py
    └── logging.py
```

---

## API Keys Setup

### Amazon PA-API

1. Sign up at https://affiliate-program.amazon.com
2. Apply for PA-API access (requires 3 sales in 180 days)
3. Get credentials from https://webservices.amazon.com/paapi5/scratchpad

### Whapi

1. Sign up at https://whapi.cloud
2. Connect your WhatsApp Business account
3. Get API key from dashboard
4. Note channel/group JIDs for recipients

### Bitly (Optional)

1. Sign up at https://bitly.com
2. Add custom domain `amzon.fyi`
3. Get API token from settings

### Keepa (Optional)

1. Sign up at https://keepa.com
2. Purchase API subscription
3. Get API key from account settings

---

## License

MIT

---

## Support

For issues, questions, or feature requests, open an issue on GitHub or contact gunn0r@gmail.com.

---

**Built with ❤️ using Python, Toga, and BeeWare**
