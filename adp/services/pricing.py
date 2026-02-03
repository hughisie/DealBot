"""Price adjustment service."""

from ..utils.config import Config
from ..utils.logging import get_logger

logger = get_logger(__name__)


class PricingService:
    """Apply price adjustment formula."""

    def __init__(self, config: Config) -> None:
        """Initialize pricing service."""
        self.config = config
        self.multiplier = config.price_multiplier
        self.additive = config.price_additive

    def adjust_price(self, validated_price: float) -> float:
        """Apply adjustment formula: FinalPrice = ValidatedPrice * multiplier + additive."""
        adjusted = validated_price * self.multiplier + self.additive
        logger.debug(
            f"Price adjustment: {validated_price} * {self.multiplier} + "
            f"{self.additive} = {adjusted}"
        )
        return round(adjusted, 2)
