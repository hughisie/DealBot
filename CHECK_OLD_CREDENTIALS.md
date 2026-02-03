# Check If Old Credentials Still Exist

## What To Do:

1. Go to: https://affiliate-program.amazon.com/home
2. Click: "Product Advertising API" → "Manage Your Credentials"
3. Look for **TWO Access Keys** in the list

### If You See Two Access Keys:

```
Access Key                | Created           | Status
AKPA0DQU0S1763063154     | Nov 13 2025 (NEW) | Active ← Getting 403
AKPA??????1763??????     | Earlier (OLD)     | Active ← Might work!
```

### If The Old Key Still Exists:

```bash
# Find what the old Access Key was
# Check your .env.backup or git history
cd "/Users/m4owen/01. Apps/07. Windsurf/03. Claude/DealBot"
git log --all -p .env 2>/dev/null | grep AMAZON_PAAPI_ACCESS_KEY | head -5
```

### Use The Old Credentials:

If you find the old Access Key, try using it:

```bash
# Update .env with OLD credentials (if you can find them)
nano .env

# Test
./venv/bin/python3 test_both_tracking_ids.py
```

---

## If Old Credentials Are Gone:

Continue to Solution 2 below...
