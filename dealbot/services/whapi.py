"""Whapi.cloud WhatsApp API integration."""

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from ..models import PublishResult
from ..utils.config import Config
from ..utils.logging import get_logger

logger = get_logger(__name__)


class WhapiService:
    """Whapi.cloud API client for WhatsApp publishing."""

    API_BASE = "https://gate.whapi.cloud"

    def __init__(self, config: Config) -> None:
        """Initialize Whapi service."""
        self.config = config
        self.api_key = config.require_env("WHAPI_API_KEY")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=4, max=30),
        reraise=True,
    )
    def send_message(
        self, destinations: list[str], message: str, deal_id: str, image_url: str = None
    ) -> PublishResult:
        """Send WhatsApp message to multiple destinations, optionally with image."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        # Whapi expects individual messages per destination
        # We'll send to each destination and collect message IDs
        message_ids: dict[str, str] = {}
        errors: list[str] = []

        for destination in destinations:
            try:
                # If image URL provided, send as image with caption
                if image_url:
                    endpoint = f"{self.API_BASE}/messages/image"
                    payload = {
                        "to": destination,
                        "media": image_url,
                        "caption": message
                    }
                    logger.info(f"Sending image message to {destination}")
                else:
                    # Otherwise send as text
                    endpoint = f"{self.API_BASE}/messages/text"
                    payload = {"to": destination, "body": message}
                    logger.info(f"Sending text message to {destination}")

                response = requests.post(
                    endpoint,
                    headers=headers,
                    json=payload,
                    timeout=30,
                )

                response.raise_for_status()
                data = response.json()

                # Extract message ID from response
                msg_id = data.get("id", data.get("message_id", "unknown"))
                message_ids[destination] = msg_id

                logger.info(f"Sent WhatsApp message to {destination}: {msg_id}")

            except requests.exceptions.HTTPError as e:
                error_msg = f"Failed to send to {destination}: {e}"
                logger.error(error_msg)
                errors.append(error_msg)
            except Exception as e:
                error_msg = f"Unexpected error sending to {destination}: {e}"
                logger.error(error_msg)
                errors.append(error_msg)

        success = len(message_ids) > 0
        error = "; ".join(errors) if errors else None

        result = PublishResult(
            deal_id=deal_id,
            destinations=destinations,
            message_ids=message_ids,
            success=success,
            error=error,
        )

        return result

    def get_recipients(self, include_group: bool = False) -> list[str]:
        """Get list of recipient JIDs based on configuration."""
        recipients = []

        channel = self.config.whatsapp_channel
        if channel:
            recipients.append(channel)

        if include_group:
            group = self.config.whatsapp_group
            if group:
                recipients.append(group)

        return recipients
