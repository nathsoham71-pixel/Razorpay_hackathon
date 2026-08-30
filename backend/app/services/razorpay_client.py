import hmac
import hashlib

import razorpay

from app.config import get_settings
from app.models.merchant import Merchant


class RazorpayIntegrationError(Exception):
    """Raised when Razorpay API calls or verification fail."""


def _resolve_keys(merchant: Merchant) -> tuple[str, str]:
    settings = get_settings()
    key_id = merchant.razorpay_key_id or settings.razorpay_key_id
    key_secret = merchant.razorpay_key_secret or settings.razorpay_key_secret
    if not key_id or not key_secret:
        raise RazorpayIntegrationError(
            "Razorpay keys not configured for merchant or global defaults"
        )
    return key_id, key_secret


def _get_client(merchant: Merchant) -> razorpay.Client:
    key_id, key_secret = _resolve_keys(merchant)
    return razorpay.Client(auth=(key_id, key_secret))


def create_test_order(amount_inr: float, receipt_id: str, merchant: Merchant) -> dict:
    """Create a Razorpay order in test mode using the merchant's keys."""
    try:
        client = _get_client(merchant)
        amount_paise = int(round(amount_inr * 100))
        order = client.order.create(
            {
                "amount": amount_paise,
                "currency": "INR",
                "receipt": receipt_id,
                "payment_capture": 1,
            }
        )
        return order
    except RazorpayIntegrationError:
        raise
    except Exception as exc:
        raise RazorpayIntegrationError(f"Failed to create Razorpay order: {exc}") from exc


def verify_payment_signature(
    order_id: str,
    payment_id: str,
    signature: str,
    merchant: Merchant,
) -> bool:
    """Verify Razorpay payment signature using HMAC SHA256."""
    try:
        _, key_secret = _resolve_keys(merchant)
        message = f"{order_id}|{payment_id}".encode()
        expected = hmac.new(
            key_secret.encode(),
            message,
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected, signature)
    except RazorpayIntegrationError:
        raise
    except Exception as exc:
        raise RazorpayIntegrationError(f"Failed to verify payment signature: {exc}") from exc
