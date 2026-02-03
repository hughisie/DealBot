"""AI-powered deal validation and product review generation using DeepSeek."""

import logging
import json
from dataclasses import dataclass
from typing import Optional
from openai import OpenAI

logger = logging.getLogger(__name__)


@dataclass
class ProductReview:
    """Bilingual product review."""
    spanish: str
    english: str


@dataclass
class AIValidationResult:
    """Result of AI validation."""
    approved: bool
    reasoning: str
    review: Optional[ProductReview] = None
    confidence: str = "medium"  # low, medium, high
    error: Optional[str] = None


class AIValidator:
    """AI-powered validation and review service using DeepSeek."""

    def __init__(self, api_key: str, model: str = "deepseek-chat"):
        """
        Initialize AI validator with DeepSeek.

        Args:
            api_key: DeepSeek API key
            model: DeepSeek model to use
        """
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com/v1"
        )
        self.model = model
        logger.info(f"AIValidator initialized with DeepSeek model: {model}")

    def validate_and_review(
        self,
        title: str,
        current_price: float,
        list_price: Optional[float],
        discount_pct: Optional[float],
        delivery_cost: Optional[float] = None,
        asin: str = None
    ) -> AIValidationResult:
        """
        Validate deal and generate product review.

        Args:
            title: Product title
            current_price: Current selling price
            list_price: Original/list price (PVP)
            discount_pct: Discount percentage
            delivery_cost: Mandatory delivery cost if any
            asin: Amazon ASIN

        Returns:
            AIValidationResult with approval and review
        """
        try:
            prompt = self._build_validation_prompt(
                title, current_price, list_price, discount_pct, delivery_cost, asin
            )

            logger.info(f"🤖 AI validating deal: {title[:50]}...")

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{
                    "role": "user",
                    "content": prompt
                }],
                temperature=0.3,  # Lower temperature for more consistent validation
                max_tokens=1024,
                response_format={"type": "json_object"}
            )

            # Parse JSON response
            response_text = response.choices[0].message.content
            result_data = json.loads(response_text)

            # Create result
            result = AIValidationResult(
                approved=result_data.get("approved", False),
                reasoning=result_data.get("reasoning", ""),
                confidence=result_data.get("confidence", "medium"),
                review=ProductReview(
                    spanish=result_data.get("review", {}).get("es", ""),
                    english=result_data.get("review", {}).get("en", "")
                ) if result_data.get("approved") else None
            )

            if result.approved:
                logger.info(f"✅ AI approved: {title[:50]}... ({result.confidence} confidence)")
            else:
                logger.warning(f"❌ AI rejected: {title[:50]}... Reason: {result.reasoning}")

            return result

        except json.JSONDecodeError as e:
            logger.error(f"AI response parsing error: {e}")
            return AIValidationResult(
                approved=False,
                reasoning="AI response parsing failed",
                error=str(e)
            )
        except Exception as e:
            logger.error(f"AI validation error: {e}")
            return AIValidationResult(
                approved=False,
                reasoning="AI validation service error",
                error=str(e)
            )

    def _build_validation_prompt(
        self,
        title: str,
        current_price: float,
        list_price: Optional[float],
        discount_pct: Optional[float],
        delivery_cost: Optional[float],
        asin: Optional[str]
    ) -> str:
        """Build validation prompt for DeepSeek."""

        delivery_note = f"\n- Mandatory delivery cost: €{delivery_cost}" if delivery_cost else ""

        prompt = f"""You are a deal validator for an Amazon deals aggregator. Analyze this deal and:
1. Validate if it's legitimate and accurate
2. Generate a brief bilingual product review (Spanish and English)

Deal Information:
- Product: {title}
- Current Price: €{current_price}
- List Price (PVP): €{list_price if list_price else 'N/A'}
- Discount: {discount_pct}%{delivery_note}
- ASIN: {asin or 'N/A'}

Validation Criteria:
1. Price Reasonableness: Does the current price match typical market prices for this product?
2. Price Consistency: Does current price vs list price match the stated discount?
3. Discount Legitimacy: Is the PVP realistic or inflated to fake a bigger discount?
4. Total Cost: If there's delivery cost, is the total still a good deal?
5. Product-Price Match: Does the price make sense for this type of product?

Review Guidelines (if approved):
- Keep reviews under 150 characters per language
- Focus on: what it is, who it's for, 1-2 key features
- Be helpful and concise
- Don't mention the price/discount in the review

Respond with valid JSON in this exact format:
{{
  "approved": true,
  "reasoning": "Brief explanation of decision",
  "confidence": "medium",
  "review": {{
    "es": "Spanish review here",
    "en": "English review here"
  }}
}}

If rejected, set approved to false and omit the "review" field.
"""
        return prompt


# Cache for AI validation results to avoid repeated API calls
_ai_validation_cache = {}


def get_cached_or_validate(
    validator: AIValidator,
    asin: str,
    title: str,
    current_price: float,
    list_price: Optional[float],
    discount_pct: Optional[float],
    delivery_cost: Optional[float] = None
) -> AIValidationResult:
    """Get cached validation or perform new validation."""
    cache_key = f"{asin}_{current_price}_{list_price}_{discount_pct}"

    if cache_key in _ai_validation_cache:
        logger.info(f"Using cached AI validation for {asin}")
        return _ai_validation_cache[cache_key]

    result = validator.validate_and_review(
        title, current_price, list_price, discount_pct, delivery_cost, asin
    )

    _ai_validation_cache[cache_key] = result
    return result
