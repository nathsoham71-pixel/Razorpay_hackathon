import json
from pathlib import Path
from typing import Any

from openai import AsyncOpenAI

from app.config import get_settings

PROMPT_PATH = (
    Path(__file__).resolve().parent.parent / "agents" / "prompts" / "merchant_agent_system_prompt.txt"
)

REQUIRED_RESPONSE_KEYS = {"reply_text", "proposed_upsell", "requested_field_changes"}


def _load_system_prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


def _validate_proposal(data: dict[str, Any]) -> dict[str, Any]:
    if not REQUIRED_RESPONSE_KEYS.issubset(data.keys()):
        missing = REQUIRED_RESPONSE_KEYS - data.keys()
        raise ValueError(f"Missing keys: {missing}")

    reply_text = data.get("reply_text")
    if not isinstance(reply_text, str):
        raise ValueError("reply_text must be a string")

    proposed = data.get("proposed_upsell")
    if proposed is not None:
        if not isinstance(proposed, dict):
            raise ValueError("proposed_upsell must be an object or null")
        for key in ("product_id", "category", "price_inr"):
            if key not in proposed:
                raise ValueError(f"proposed_upsell missing {key}")

    field_changes = data.get("requested_field_changes")
    if not isinstance(field_changes, list):
        raise ValueError("requested_field_changes must be a list")

    return {
        "reply_text": reply_text,
        "proposed_upsell": proposed,
        "requested_field_changes": field_changes,
    }


async def propose_upsell(
    conversation_history: list[dict[str, Any]],
    cart_context: dict[str, Any],
    available_upsell_products: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    GPT wrapper that ONLY proposes upsells — it has ZERO authority to approve spend.

    Mandate enforcement happens separately in mandate_engine.check_upsell_against_mandate()
    after this function returns. No amount of prompt engineering can bypass that check.
    """
    settings = get_settings()
    if not settings.openai_api_key:
        return {
            "reply_text": "Merchant agent is unavailable (OPENAI_API_KEY not configured).",
            "proposed_upsell": None,
            "requested_field_changes": [],
        }

    client = AsyncOpenAI(api_key=settings.openai_api_key)
    system_prompt = _load_system_prompt()

    user_payload = {
        "cart_context": cart_context,
        "available_upsell_products": available_upsell_products,
        "conversation_history": conversation_history,
    }

    messages: list[dict[str, Any]] = [
        {"role": "system", "content": system_prompt},
        *conversation_history,
        {
            "role": "user",
            "content": json.dumps(user_payload, default=str),
        },
    ]

    for attempt in range(2):
        try:
            response = await client.chat.completions.create(
                model=settings.openai_model,
                messages=messages,
                response_format={"type": "json_object"},
                temperature=0.4,
            )
            raw = response.choices[0].message.content or "{}"
            parsed = json.loads(raw)
            return _validate_proposal(parsed)
        except (json.JSONDecodeError, ValueError, KeyError) as exc:
            if attempt == 0:
                messages.append(
                    {
                        "role": "system",
                        "content": (
                            f"Your previous response was invalid: {exc}. "
                            "Respond again with valid JSON matching the required schema exactly."
                        ),
                    }
                )
                continue
            return {
                "reply_text": "Sorry, I couldn't process that request right now. Please try again.",
                "proposed_upsell": None,
                "requested_field_changes": [],
            }
        except Exception as exc:
            return {
                "reply_text": f"Merchant agent error: {exc}",
                "proposed_upsell": None,
                "requested_field_changes": [],
            }

    return {
        "reply_text": "Sorry, I couldn't process that request right now.",
        "proposed_upsell": None,
        "requested_field_changes": [],
    }
