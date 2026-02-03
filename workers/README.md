# Cloudflare Workers Short Link Service

Alternative to Bitly for creating short links on `amzon.fyi` domain.

## Setup

1. **Install Wrangler CLI**
   ```bash
   npm install -g wrangler
   ```

2. **Authenticate**
   ```bash
   wrangler login
   ```

3. **Create KV Namespace**
   ```bash
   wrangler kv:namespace create "LINKS"
   ```

   Note the ID from output and update `wrangler.toml`.

4. **Deploy Worker**
   ```bash
   cd workers
   wrangler deploy
   ```

5. **Add Custom Domain**
   - Go to Cloudflare dashboard
   - Add `amzon.fyi` as custom domain for the worker

6. **Set Environment Variables**
   Add to `.env`:
   ```bash
   CLOUDFLARE_ACCOUNT_ID=your_account_id
   CLOUDFLARE_API_TOKEN=your_api_token
   ```

## Usage

The Worker provides two endpoints:

**POST /shorten** - Create short link
```bash
curl -X POST https://amzon.fyi/shorten \
  -H "Content-Type: application/json" \
  -d '{"url": "https://amazon.es/dp/B08N5WRWNW", "slug": "abc123"}'
```

**GET /:slug** - Redirect or serve interstitial
```bash
curl https://amzon.fyi/abc123
```

## Notes

- KV storage is eventually consistent (typically <60s)
- Free tier: 100,000 reads/day, 1,000 writes/day
- For production, consider Cloudflare Pro for better limits
