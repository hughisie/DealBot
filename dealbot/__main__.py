"""Entry point for DealBot macOS app."""
from dealbot.app import main

if __name__ == "__main__":
    app = main()
    app.main_loop()
