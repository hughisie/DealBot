# DealBot Setup Guide

Complete setup instructions for getting DealBot running on macOS.

---

## Prerequisites

- macOS 11.0 or later
- Python 3.11 or later
- Homebrew (recommended)

---

## Step 1: Install Python

```bash
brew install python@3.11
```

Verify installation:
```bash
python3 --version  # Should show 3.11.x or later
```

---

## Step 2: Setup Project

```bash
cd "/Users/m4owen/01. Apps/07. Windsurf/03. Claude/DealBot"
make setup
```

This will:
- Create a virtual environment in `venv/`
- Install all dependencies from `pyproject.toml`
- Install development dependencies (pytest, black, ruff, mypy)

---

## Step 3: Configure Environment Variables

1. **Copy the example environment file:**
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` and add your API keys:**
   ```bash
   # Required
   WHAPI_API_KEY=your_whapi_key_here
   AMAZON_PAAPI_SECRET_KEY=your_secret_key_here
   AMAZON_ASSOCIATE_TAG=yourtagname-21
   
   # Optional (choose one for short links)
   BITLY_TOKEN=your_bitly_token_here
   # OR
   CLOUDFLARE_ACCOUNT_ID=your_account_id
   CLOUDFLARE_API_TOKEN=your_api_token
   
   # Optional (for ratings)
   KEEPA_API_KEY=your_keepa_key
   ```

---

## Step 4: Configure Application Settings

Edit `config.yaml` to customize:

```yaml
# Update this path to your Google Drive deals folder
default_source_dir: "/Users/m4owen/Library/CloudStorage/GoogleDrive-gunn0r@gmail.com/Shared drives/01.Player Clothing Team Drive/02. RetroShell/13. Articles and Data/09. Feed Finder/amazon_deals"

# Adjust price formula if needed
price_adjustment:
  multiplier: 1.00  # e.g., 1.10 for 10% markup
  additive: 0.00    # e.g., 5.00 to add €5

# Confirm WhatsApp recipients
whatsapp:
  recipients:
    channel: "0029Vb6PJDh6WaKjaAcWAX1h@broadcast"
    group: "120363269876975950@g.us"
  send_to_group: false

# Choose short link provider
shortlinks:
  provider: "bitly"  # or "cloudflare"
  domain: "amzon.fyi"
```

---

## Step 5: Test the Application

Run in development mode:
```bash
make run
```

The Toga GUI should open. Try:
1. Click "Select TXT File"
2. Choose `example_deals.txt`
3. Review parsed deals in the table
4. (Optional) Click "Process & Publish Selected" to test full pipeline

**Note**: Publishing will fail if API keys are not configured correctly.

---

## Step 6: Package as macOS App

Once everything is working, package the app:

```bash
make package
```

This creates:
- `build/dealbot/macos/app/DealBot.app` - The macOS application bundle

**To install:**
1. Copy `DealBot.app` to your `/Applications` folder
2. Launch from Launchpad or Spotlight

**First Launch Note**: macOS may show a security warning. Go to System Preferences → Security & Privacy → General and click "Open Anyway".

---

## Troubleshooting

### "Command not found: make"
Install Xcode Command Line Tools:
```bash
xcode-select --install
```

### "ModuleNotFoundError" when running
Ensure you're using the virtual environment:
```bash
source venv/bin/activate
python -m adp.app
```

### "Configuration Error" in app
Check that `config.yaml` exists and is valid YAML syntax.

### "Required environment variable not set"
Verify `.env` file exists and contains all required keys.

### Amazon PA-API 403 errors
- Verify your PA-API credentials are correct
- Ensure you have an active Amazon Associates account
- PA-API requires 3 sales in the last 180 days

### Whapi 401 errors
- Check your `WHAPI_API_KEY` in `.env`
- Verify your Whapi account is active
- Ensure your WhatsApp Business account is connected

### Bitly 403 errors
- Verify `BITLY_TOKEN` is valid
- Check that `amzon.fyi` domain is connected to your Bitly account

---

## Running Tests

```bash
make test
```

Run specific test file:
```bash
./venv/bin/pytest tests/test_parsing.py -v
```

---

## Development Workflow

1. **Make code changes** in `adp/` directory
2. **Format code**: `make format`
3. **Run linter**: `make lint`
4. **Run tests**: `make test`
5. **Test in GUI**: `make run`
6. **Package**: `make package`

---

## Database Location

SQLite database is created at: `dealbot.db`

To view:
- **In app**: Tools → Open Database
- **SQLite Browser**: Download from https://sqlitebrowser.org
- **Command line**: `sqlite3 dealbot.db`

---

## Updating Configuration

### To change price formula
Edit `config.yaml` → `price_adjustment` section

### To add/remove WhatsApp recipients
Edit `config.yaml` → `whatsapp.recipients`

### To switch short link providers
1. Edit `config.yaml` → `shortlinks.provider`
2. Ensure corresponding API token is in `.env`

### To enable/disable ratings
Edit `config.yaml` → `ratings.enabled`

---

## Next Steps

1. ✅ **Configure all API keys** in `.env`
2. ✅ **Test with example_deals.txt**
3. ✅ **Verify WhatsApp publishing works**
4. ✅ **Set up Bitly branded domain** (or Cloudflare Worker)
5. ✅ **Customize price adjustment formula**
6. ✅ **Package as .app and install**
7. ✅ **Create your first real deal file**

---

## Support Resources

- **Amazon PA-API Docs**: https://webservices.amazon.com/paapi5/documentation/
- **Whapi Docs**: https://whapi.readme.io
- **Bitly API**: https://dev.bitly.com
- **Toga Docs**: https://toga.readthedocs.io
- **Briefcase Docs**: https://briefcase.readthedocs.io

---

**Ready to publish deals! 🚀**
