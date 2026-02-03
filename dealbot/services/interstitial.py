"""Interstitial page server using FastAPI."""

import asyncio
import threading
from pathlib import Path
from typing import Optional

import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, RedirectResponse
from jinja2 import Template

from ..utils.config import Config
from ..utils.logging import get_logger

logger = get_logger(__name__)


class InterstitialServer:
    """FastAPI server for interstitial landing pages."""

    def __init__(self, config: Config, host: str = "127.0.0.1", port: int = 8765) -> None:
        """Initialize interstitial server."""
        self.config = config
        self.host = host
        self.port = port
        self.app = FastAPI()
        self.template = self._load_template()
        self._setup_routes()
        self._server_thread: Optional[threading.Thread] = None

    def _load_template(self) -> Template:
        """Load Jinja2 template for interstitial page."""
        template_path = Path(__file__).parent.parent / "ui" / "templates" / "interstitial.html.j2"
        if template_path.exists():
            with open(template_path, "r") as f:
                return Template(f.read())
        else:
            # Fallback inline template
            return Template(self._get_default_template())

    def _get_default_template(self) -> str:
        """Get default interstitial HTML template."""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Redirecting to Amazon...</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        .container {
            text-align: center;
            background: white;
            padding: 3rem;
            border-radius: 1rem;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            max-width: 500px;
        }
        h1 {
            color: #333;
            margin-bottom: 1rem;
        }
        .deal-info {
            margin: 2rem 0;
            padding: 1.5rem;
            background: #f8f9fa;
            border-radius: 0.5rem;
        }
        .price {
            font-size: 2.5rem;
            color: #667eea;
            font-weight: bold;
        }
        .countdown {
            font-size: 1.2rem;
            color: #666;
            margin: 1rem 0;
        }
        .btn {
            display: inline-block;
            padding: 1rem 2rem;
            background: #667eea;
            color: white;
            text-decoration: none;
            border-radius: 0.5rem;
            font-weight: bold;
            margin-top: 1rem;
        }
        .btn:hover {
            background: #5568d3;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🛍️ Great Deal Found!</h1>
        <div class="deal-info">
            <div style="font-size: 1.2rem; margin-bottom: 0.5rem;">{{ title }}</div>
            <div class="price">{{ currency }}{{ price }}</div>
        </div>
        <div class="countdown">Redirecting in <span id="timer">{{ countdown }}</span> seconds...</div>
        <a href="{{ destination }}" class="btn">Continue to Amazon Now</a>
    </div>
    <script>
        let countdown = {{ countdown }};
        const timerEl = document.getElementById('timer');
        const interval = setInterval(() => {
            countdown--;
            timerEl.textContent = countdown;
            if (countdown <= 0) {
                clearInterval(interval);
                window.location.href = '{{ destination }}';
            }
        }, 1000);
    </script>
</body>
</html>
"""

    def _setup_routes(self) -> None:
        """Setup FastAPI routes."""

        @self.app.get("/i/{deal_id}")
        async def interstitial(deal_id: str) -> HTMLResponse:
            """Serve interstitial page (for local testing)."""
            # In production, this would fetch deal data from database
            html = self.template.render(
                title="Amazing Deal",
                price="49.99",
                currency="€",
                destination="https://amazon.com",
                countdown=self.config.interstitial_countdown,
            )
            return HTMLResponse(content=html)

        @self.app.get("/health")
        async def health() -> dict[str, str]:
            """Health check endpoint."""
            return {"status": "ok"}

    def start(self) -> None:
        """Start server in background thread."""
        if self._server_thread and self._server_thread.is_alive():
            logger.info("Interstitial server already running")
            return

        def run_server() -> None:
            uvicorn.run(self.app, host=self.host, port=self.port, log_level="warning")

        self._server_thread = threading.Thread(target=run_server, daemon=True)
        self._server_thread.start()
        logger.info(f"Interstitial server started at http://{self.host}:{self.port}")

    def stop(self) -> None:
        """Stop server (graceful shutdown not implemented for daemon thread)."""
        logger.info("Interstitial server stopping (daemon thread will terminate with app)")

    def get_interstitial_url(self, deal_id: str) -> str:
        """Get interstitial URL for a deal."""
        return f"http://{self.host}:{self.port}/i/{deal_id}"
