/**
 * Cloudflare Worker for short link management
 * Handles /shorten (create) and /:slug (redirect/interstitial)
 */

const INTERSTITIAL_HTML = `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Redirecting to Amazon...</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 1rem;
        }
        .container {
            text-align: center;
            background: white;
            padding: 3rem 2rem;
            border-radius: 1.5rem;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            max-width: 600px;
            width: 100%;
            animation: slideUp 0.5s ease-out;
        }
        @keyframes slideUp {
            from { opacity: 0; transform: translateY(30px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .logo { font-size: 4rem; margin-bottom: 1rem; }
        h1 { color: #333; margin-bottom: 1.5rem; font-size: 2rem; }
        .countdown {
            font-size: 1.3rem;
            color: #666;
            margin: 2rem 0;
            font-weight: 500;
        }
        #timer { color: #667eea; font-weight: bold; font-size: 1.5rem; }
        .btn {
            display: inline-block;
            padding: 1.2rem 2.5rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            text-decoration: none;
            border-radius: 0.75rem;
            font-weight: bold;
            font-size: 1.1rem;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
        }
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">🛍️</div>
        <h1>Great Deal Found!</h1>
        <div class="countdown">
            Redirecting in <span id="timer">2</span> seconds...
        </div>
        <a href="{{DESTINATION}}" class="btn">Continue to Amazon Now →</a>
    </div>
    <script>
        let countdown = 2;
        const timerEl = document.getElementById('timer');
        const interval = setInterval(() => {
            countdown--;
            timerEl.textContent = countdown;
            if (countdown <= 0) {
                clearInterval(interval);
                window.location.href = '{{DESTINATION}}';
            }
        }, 1000);
    </script>
</body>
</html>
`;

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    
    // Health check (check first)
    if (url.pathname === '/' || url.pathname === '/health') {
      return new Response(JSON.stringify({ status: 'ok' }), {
        headers: { 'Content-Type': 'application/json' },
      });
    }
    
    // POST /shorten - Create short link
    if (request.method === 'POST' && url.pathname === '/shorten') {
      try {
        const body = await request.json();
        const { url: longUrl, slug } = body;
        
        if (!longUrl || !slug) {
          return new Response(JSON.stringify({ error: 'Missing url or slug' }), {
            status: 400,
            headers: { 'Content-Type': 'application/json' },
          });
        }
        
        // Store in KV
        await env.LINKS.put(slug, longUrl);
        
        const shortUrl = `${url.origin}/${slug}`;
        
        return new Response(JSON.stringify({ short_url: shortUrl, slug }), {
          status: 201,
          headers: { 'Content-Type': 'application/json' },
        });
      } catch (err) {
        return new Response(JSON.stringify({ error: err.message }), {
          status: 500,
          headers: { 'Content-Type': 'application/json' },
        });
      }
    }
    
    // GET /:slug - Redirect with interstitial
    if (request.method === 'GET' && url.pathname !== '/' && url.pathname !== '/shorten') {
      const slug = url.pathname.slice(1);
      const longUrl = await env.LINKS.get(slug);
      
      if (!longUrl) {
        return new Response('Short link not found', { status: 404 });
      }
      
      // Serve interstitial HTML with countdown
      const html = INTERSTITIAL_HTML.replace(/{{DESTINATION}}/g, longUrl);
      
      return new Response(html, {
        headers: { 'Content-Type': 'text/html' },
      });
    }
    
    return new Response('Not found', { status: 404 });
  },
};
